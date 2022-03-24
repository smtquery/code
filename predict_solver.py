import tempfile
from collections import Counter

import smtquery.config
import numpy
import numpy as np
import torch
import smtquery.storage.smt.db
from smtquery.intel.plugins import probes
import smtquery.smtcon.exprfun
import smtquery.solvers
import smtquery.utils.pattern
from smtquery.smtcon.expr import Kind, Sort
from smtquery.smtcon.smt2expr import Z3SMTtoSExpr

db = 'sqlite:///db.sql'
storage = smtquery.storage.smt.db.DBFSStorage('.', db)

smtprobe = Z3SMTtoSExpr()
intels = {
    'atoms': (smtquery.smtcon.exprfun.HasAtom(), dict()),
    'bounds': (smtquery.smtcon.exprfun.Bounded(), []),
    'reglen': (smtquery.smtcon.exprfun.RegExLengths(), []),
    'patmat': (smtquery.smtcon.exprfun.PatternMatching(), [])
}

def extract_attributes(smtfile):
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = smtfile.copyOutSMTFile(tmpdir)
        ast = smtprobe.getAST(filepath)
        assert isinstance(ast, smtquery.smtcon.expr.ASTRef)

        features = []
        for name, probe in intels.items():
            ast.add_intel_with_function(probe[0].apply, probe[0].merge, probe[1], name)
        # number of assertions
        features += [len(ast.get_intel()['patmat'])]
        # number of variables
        if Kind.VARIABLE in ast.get_intel()['atoms']:
            features += [ast.get_intel()['atoms'][Kind.VARIABLE]]
        else:
            features += [0]
        # proportion ofword equations, length constraints, regex constraints, high level funs
        total = sum([v for k, v in ast.get_intel()['atoms'].items() if k not in [Kind.OTHER, Kind.VARIABLE, Kind.CONSTANT]])
        for kind in [Kind.WEQ, Kind.LENGTH_CONSTRAINT, Kind.REGEX_CONSTRAINT, Kind.HOL_FUNCTION]:
            if kind in ast.get_intel()['atoms']:
                features += [ast.get_intel()['atoms'][kind]/total]
            else:
                features += [0]
        # upper bound of string variables
        if Sort.String in ast.get_intel()['variables']:
            vs = ast.get_intel()['variables'][Sort.String]
            lens = {v: float('inf') for v in vs}
            for bound_dict in ast.get_intel()['bounds']:
                if 'lc' in bound_dict:
                    for v, (_, u) in bound_dict['lc'].items():
                        lens[v] = u
                if 'weq' in bound_dict:
                    for v, (_, u) in bound_dict['weq'].items():
                        lens[v] = u
                if 'rel' in bound_dict:
                    for v, cons in bound_dict['rel'].items():
                        for op, w in cons:
                            if (op == '=' or op == '<=' or op == '<') and lens[w] != float('inf'):
                                lens[v] = lens[w]
            if max(lens.values()) == float('inf'):
                features += [-1]
            else:
                features += [max(lens.values())]
        else:
            features += [0]
        # length of involved regular expressions
        features += [sum(ast.get_intel()['reglen'])]
        # max degree and number of pattern matching problems
        true_matching = 0
        max_degree = 0
        for x in ast.get_intel()['patmat']:
            if x != 'non_matching':
                l, r = x
                if isinstance(l, smtquery.utils.pattern.Variable) and isinstance(r, smtquery.utils.pattern.Pattern):
                    if l.v not in r.vs:
                        true_matching += 1
                    max_degree = max(1, max_degree, max(list(Counter(r.vs).values()), default=0))
                elif isinstance(l, smtquery.utils.pattern.Pattern) and isinstance(r, smtquery.utils.pattern.Variable):
                    if r.v not in l.vs:
                        true_matching += 1
                    max_degree = max(1, max_degree, max(list(Counter(l.vs).values()), default=0))
                elif isinstance(l, smtquery.utils.pattern.Pattern) and isinstance(r, smtquery.utils.pattern.Pattern):
                    max_degree = max(max_degree,
                                     max(list(Counter(l.vs).values()) + list(Counter(r.vs).values()), default=0))
                else:
                    if l.v != r.v:
                        true_matching += 1
                    max_degree = max(1, max_degree)
        features += [true_matching, max_degree]

    return features


def choose_solver(results):
    l = [(i, r.getResult(), r.getTime()) for i, r in enumerate(results)]
    if all([r.getResult().value < 2 for r in results]):
        if l[0][1] != l[1][1] or l[0][1] != l[2][1] or l[1][1] != l[2][1]:
            print(results)
    m = min(l, key=lambda x: (x[1].value, x[2]))
    if m[1].value < 2:
        return m[0]


# filelocator = smtquery.config.FileLocator(['./data/conf'])
# with open(filelocator.findFile('conf.yml')) as f:
#     smtquery.config.readConfig(f)

cvc4 = smtquery.solvers.createSolver('CVC4', 'bin/cvc4.exe')
z3str3 = smtquery.solvers.createSolver('Z3Str3', 'venv3.9/bin/z3.exe')
z3seq = smtquery.solvers.createSolver('Z3Seq', 'venv3.9/bin/z3.exe')

solvers = [cvc4, z3str3, z3seq]

bench = 'stringfuzz'
test_instances = [i for b in storage.getBenchmarks() if b.getName() == bench for t in b.tracksInBenchmark()
                  for i in t.filesInTrack()]
n_inst = len(test_instances)
n_feat = 10
data = np.empty((0, n_feat+1))

for i, inst in enumerate(test_instances):
    print(f'{i+1}/{n_inst}:{inst.getName()}')
    features = extract_attributes(inst)
    target = choose_solver([s.runSolver(inst, timeout=2) for s in solvers])
    if target is not None:
        data = np.vstack((data, features+[target]))
    else:
        print('UNKNOWN|TIMEOUT|ERROR')

np.savetxt(f'training_data/{bench}.csv', data, delimiter=',', fmt='%.5f')