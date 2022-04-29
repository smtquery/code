import smtquery.solvers.solver as solver
import subprocess

class Z3(solver.Solver):
    def __init__(self,binarypath,variation = "Str3",stringsolver ="z3str3"):
        super().__init__(binarypath)
        self._path = binarypath
        self._variation = variation
        self._stringsolver = stringsolver
        
    def getVersion (self):
        return subprocess.check_output ([self._path,"--version"])

    def getName (self):
        return "Z3"+self._variation
    
    def preprocessSMTFile  (self, origsmt, newsmt):
        with open(origsmt,'r') as orig, open(newsmt,'w') as new:
            for l in orig:
                if "(get-model" not in l:
                    new.write (l)

    def buildCMDList (self,smtfilepath):
        return [self._path,f"smt.string_solver={self._stringsolver}","dump_models=true",smtfilepath]



