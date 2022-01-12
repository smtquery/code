
import smtquery.smtcon.smt2expr
import smtquery.smtcon.exprfun
from smtquery.smtcon.expr import Kind
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

    def _storeAST(self,smtfile,ast):
        rel_filepath = ''.join(f"/{f}" for f in smtfile.getName().split(":")[:-1])
        filename = smtfile.getName().split(":")[-1]
        pickle_file_path = f"{self._pickleBasePath}{rel_filepath}/{smtfile.hashContent()}_{filename}.pickle"
        with open(pickle_file_path, 'wb') as handle:
            pickle.dump(ast, handle, protocol=pickle.HIGHEST_PROTOCOL)

    def getAST(self,smtfile,filepath):
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
            self._storeAST(smtfile,ast)

    def getIntel (self, smtfile):
        with tempfile.TemporaryDirectory () as tmpdir:
            filepath = smtfile.copyOutSMTFile (tmpdir)
            pr = self.getAST(smtfile,filepath)
            for (name,c) in self.intels().items():
                self.addIntel(smtfile,pr,c[0],c[1],name)
            return pr

    def intels (self):
        t = dict()
        return {
            "has" : (smtquery.smtcon.exprfun.HasAtom(),t),
            "#variables" : (smtquery.smtcon.exprfun.VariableCount(),dict()),
            "pathVars" : (smtquery.smtcon.exprfun.VariableCountPath(),[])
        }

    def predicates (self):
        return {
            "hasWEQ" : partial(hasKind,Kind.WEQ),
            "hasLinears" : partial(hasKind,Kind.LENGTH_CONSTRAINT),
            "hasRegex" : partial(hasKind,Kind.REGEX_CONSTRAINT)
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


def makePlugin ():
    return Probes
