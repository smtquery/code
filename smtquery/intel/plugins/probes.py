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
import logging
from smtquery.qlang.trool import *
import smtquery.predicates.predicates
from datetime import datetime


class Probes:
    def __init__(self):
        super().__init__ ()
        self._smtprobe = smtquery.smtcon.smt2expr.Z3SMTtoSExpr ()
        self._pickleBasePath = "smtquery/data/pickle"
        self.use_cache = True
        self.intel_key_map = dict()

    def _storeAST(self,smtfile,ast):
        logging.debug(f"writing AST for {smtfile.getName()}")
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
        logging.debug(f"accessing {smtfile.getName()} as pickle file {pickle_file_path}")

        if not os.path.exists(self._pickleBasePath+rel_filepath):
            try:
                os.makedirs(self._pickleBasePath+rel_filepath)
            except Exception as e:
                pass
            
        if os.path.isfile(pickle_file_path):
            logging.debug("found pickle file")
            with open(pickle_file_path, 'rb') as handle:
                return pickle.load(handle)
        else:
            logging.debug("build AST")
            pr = self._smtprobe.getAST (filepath)
            self._storeAST(smtfile,pr)
            return pr
   
    def addIntel(self,smtfile,ast,plugin,name):
        if name not in ast.intel.keys():
            ast.add_intel_with_function(plugin().apply,plugin().merge,plugin().neutral(),name)
            if self.use_cache:
                self._storeAST(smtfile,ast)

    def getIntel (self, smtfile, i_classes):
        with tempfile.TemporaryDirectory () as tmpdir:
            filepath = smtfile.copyOutSMTFile (tmpdir)
            pr = self.getAST(smtfile,filepath)

            for i_class in i_classes:
                # reserve a new intel identifier
                if str(i_class) not in self.intel_key_map.keys():
                    self.intel_key_map[str(i_class)] = len(self.intel_key_map.keys())

                # calculate intel if needed
                self.addIntel(smtfile,pr,i_class,self.intel_key_map[str(i_class)])

            #print(pr.get_intel())
            return pr
        
    def getIntelKey2Class(self,i_class):
        # we might want to initialise the intel of i_class here... --> call getIntel()!                
        if str(i_class) not in self.intel_key_map.keys():
                self.intel_key_map[str(i_class)] = len(self.intel_key_map.keys())
        return self.intel_key_map[str(i_class)]



    def intels (self):
        pass
        
        
        """return {
            "has" : (smtquery.smtcon.exprfun.HasAtom(),dict()),
            "regex" : (smtquery.smtcon.exprfun.RegexStructure(),dict()),
            "variables" : (smtquery.smtcon.exprfun.VariableCount(),dict()),
            "pathVars" : (smtquery.smtcon.exprfun.VariableCountPath(),[])
        }"""

    def predicates (self):
        p = Probes()
        return {
            "hasWEQ" : smtquery.predicates.predicates.HasWEQ(p),
            "hasLinears" : smtquery.predicates.predicates.HasLinears(p),
            "hasRegex" : smtquery.predicates.predicates.HasRegex(p),
            "hasHOL" : smtquery.predicates.predicates.HasHOL(p),
            "hasAtLeast5Variables" : smtquery.predicates.predicates.HasAtLeastCountVariables(p),
            "isQuadratic" : smtquery.predicates.predicates.IsQuadratic(p),    
        }
        """return {
            "isQuadratic" : isQuadratic,
            "hasWEQ" : partial(hasKind,Kind.WEQ),
            "hasLinears" : partial(hasKind,Kind.LENGTH_CONSTRAINT),
            "hasRegex" : partial(hasKind,Kind.REGEX_CONSTRAINT),
            "hasHOL" : partial(hasKind,Kind.HOL_FUNCTION),
            "isSimpleRegex" : lambda smtfile: TroolAnd(isSimpleRegex(smtfile), TroolAnd(TroolNot(hasConcatenationRegex(smtfile)),TroolAnd(TroolNot(hasKind(Kind.WEQ,smtfile)),TroolNot(hasKind(Kind.LENGTH_CONSTRAINT,smtfile))))),
            "isSimRegexConcatenation" : lambda smtfile: TroolAnd(isSimpleRegex(smtfile), TroolAnd(hasConcatenationRegex(smtfile),TroolAnd(TroolNot(hasKind(Kind.WEQ,smtfile)),TroolNot(hasKind(Kind.LENGTH_CONSTRAINT,smtfile))))),
            "hasAtLeast5Variables" :  lambda smtfile: (hasAtLeastCountStringVariables(smtfile,5))
        }"""

    @staticmethod
    def getName ():
        return "Probes"

    @staticmethod
    def getVersion ():
        return "0.0.1"


### hier weiter!!!
# Regex
def isSimpleRegex(smtfile):
    if not Probes().getIntel(smtfile).get_intel()["regex"]["complement"]:
        return smtquery.qlang.predicates.Trool.TT
    else:
        return smtquery.qlang.predicates.Trool.FF

def hasConcatenationRegex(smtfile):
    if Probes().getIntel(smtfile).get_intel()["regex"]["concatenation"]:
        return smtquery.qlang.predicates.Trool.TT
    else:
        return smtquery.qlang.predicates.Trool.FF

def makePlugin ():
    return Probes
