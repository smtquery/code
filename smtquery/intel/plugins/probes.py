
import smtquery.smtcon.smt2expr
import smtquery.smtcon.exprfun
from smtquery.smtcon.expr import Kind
from smtquery.smtcon.expr import Sort
import smtquery.qlang.predicates
import os
import pickle
import tempfile
import smtquery.smtcon.smt2expr
from functools import partial



class Probes:
    def __init__(self):
        super().__init__ ()
        self._smtprobe = smtquery.smtcon.smt2expr.Z3SMTtoSExpr ()
        self._pickleBasePath = "smtquery/data/pickle"
        self.use_cache = True

    def _storeAST(self,smtfile,ast):
        rel_filepath = ''.join(f"/{f}" for f in smtfile.getName().split(":")[:-1])
        filename = smtfile.getName().split(":")[-1]
        pickle_file_path = f"{self._pickleBasePath}{rel_filepath}/{smtfile.hashContent()}_{filename}.pickle"
        with open(pickle_file_path, 'wb') as handle:
            pickle.dump(ast, handle, protocol=pickle.HIGHEST_PROTOCOL)

    def getAST(self,smtfile,filepath):
        # for testing purpose
        if not self.use_cache:
            return self._smtprobe.getAST (filepath)

        rel_filepath = ''.join(f"/{f}" for f in smtfile.getName().split(":")[:-1])
        filename = smtfile.getName().split(":")[-1]
        pickle_file_path = f"{self._pickleBasePath}{rel_filepath}/{smtfile.hashContent()}_{filename}.pickle"
        if not os.path.exists(self._pickleBasePath+rel_filepath):
            os.makedirs(self._pickleBasePath+rel_filepath)
        if os.path.isfile(pickle_file_path):
            with open(pickle_file_path, 'rb') as handle:
                return pickle.load(handle)
        else:
            pr = self._smtprobe.getAST (filepath)
            self._storeAST(smtfile,pr)
            return pr
   
    def addIntel(self,smtfile,ast,plugin,neutral_element,name):
        if name not in ast.intel.keys():
            ast.add_intel_with_function(plugin.apply,plugin.merge,neutral_element,name)
            if self.use_cache:
                self._storeAST(smtfile,ast)

    def getIntel (self, smtfile):
        with tempfile.TemporaryDirectory () as tmpdir:
            filepath = smtfile.copyOutSMTFile (tmpdir)
            pr = self.getAST(smtfile,filepath)
            for (name,c) in self.intels().items():
                self.addIntel(smtfile,pr,c[0],c[1],name)
            return pr

    def intels (self):
        return {
            "has" : (smtquery.smtcon.exprfun.HasAtom(),dict()),
            "regex" : (smtquery.smtcon.exprfun.RegexStructure(),dict()),
            "#variables" : (smtquery.smtcon.exprfun.VariableCount(),dict()),
            "pathVars" : (smtquery.smtcon.exprfun.VariableCountPath(),[])
        }

    def predicates (self):
        return {
            "isQuadratic" : isQuadratic,
            "hasWEQ" : partial(hasKind,Kind.WEQ),
            "hasLinears" : partial(hasKind,Kind.LENGTH_CONSTRAINT),
            "hasRegex" : partial(hasKind,Kind.REGEX_CONSTRAINT),
            "isSimpleRegex" : lambda smtfile: (isSimpleRegex(smtfile) and not hasConcatenationRegex(smtfile) and TroolNot(partial(hasKind,Kind.WEQ)) and TroolNot(partial(hasKind,Kind.LENGTH_CONSTRAINT))) == True,
            "isSimpleRegexConcatenation" : lambda smtfile: (isSimpleRegex(smtfile) and hasConcatenationRegex(smtfile) and TroolNot(partial(hasKind,Kind.WEQ)) and TroolNot(partial(hasKind,Kind.LENGTH_CONSTRAINT))) == True
        }

    @staticmethod
    def getName ():
        return "Probes"

    

    @staticmethod
    def getVersion ():
        return "0.0.1"
    
def hasKind(kind,smtfile):
    if kind in smtfile.Probes.get_intel()["has"]:
        return smtquery.qlang.predicates.Trool.TT
    else:
        return smtquery.qlang.predicates.Trool.FF

# Regex
def isSimpleRegex(smtfile):
    if not smtfile.Probes.get_intel()["regex"]["complement"]:
        return smtquery.qlang.predicates.Trool.TT
    else:
        return smtquery.qlang.predicates.Trool.FF

def hasConcatenationRegex(smtfile):
    if not smtfile.Probes.get_intel()["regex"]["concatenation"]:
        return smtquery.qlang.predicates.Trool.TT
    else:
        return smtquery.qlang.predicates.Trool.FF

def isQuadratic(smtfile,max_vars=2):
    qudratic = True

    """
    # check quadtratic without repecting the paths
    vcs = smtfile.Probes.get_intel()["#variables"]
    if Sort.String in vcs:
        if not all([vcs[Sort.String][var] <= max_vars for var in vcs[Sort.String].keys()]):
            return smtquery.qlang.predicates.Trool.FF
    return smtquery.qlang.predicates.Trool.TT
    """

    for pv in [pv[Sort.String] for pv in smtfile.Probes.get_intel()["pathVars"] if Sort.String in pv]:
        qudratic = qudratic and all([pv[var] <= max_vars for var in pv.keys()])
    if qudratic:
        return smtquery.qlang.predicates.Trool.TT
    else:
        return smtquery.qlang.predicates.Trool.FF

def makePlugin ():
    return Probes
