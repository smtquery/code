import smtquery.smtcon.smt2expr
import tempfile
import enum
import os

class Validated(enum.Enum):
    Validated = 0
    NotValidated = 1

class Verifier:
    def __init__(self,solver):
        self._solver = solver

    def verifyModel (self,smtfile,model,timeout = None):
        ass_model = self._extractAssignment (model)
        ast = smtquery.smtcon.smt2expr.Z3SMTtoSExpr ().getAST (smtfile.getFilepath ())
        smt_ver_text = f"{ast._getPPSMTHeader()}\n{ass_model}\n{ast._getPPAsserts()}\n{ast._getPPSMTFooter()}"
        with tempfile.TemporaryDirectory () as tmppath:
            smtpath = os.path.join (tmppath,"inp.smt")
            with open(smtpath,'w') as ff:
                ff.write (smt_ver_text)
            verresult = self._solver.runSolverOnPath (smtpath,timeout)
        if verresult.getResult () == smtquery.solvers.solver.Result.Satisfied:
            return Validated.Validated
        else:
            
            return Validated.NotValidated
        
        
    def _extractAssignment(self,model):
        s = ""
        for l in model:
            s+=l.rstrip("\n")
        if s.startswith("(model"):
            return s[len("(model"):-1]
        elif s.startswith("sat("):
            return s[len("sat("):-1]
        else:
            return s[len("("):-1]
        
