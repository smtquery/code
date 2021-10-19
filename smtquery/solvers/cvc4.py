import smtquery.solvers.solver as solver
import subprocess

class CVC4(solver.Solver):
    def __init__(self,binarypath):
        super().__init__(binarypath)
        self._path = binarypath
        
    def getVersion (self):
        return subprocess.check_output ([self._path,"--version"])

    def getName (self):
        return "CVC4"
    
    def preprocessSMTFile  (self, origsmt, newsmt):
        with open(origsmt,'r') as orig, open(newsmt,'w') as new:
            firstline = True
            for l in orig:
                if not l.startswith (";") and firstline:
                    firstline = False
                    if "(set-logic" not in l:
                        new.write ("(set-logic ALL)\n")
                    else:
                        new.write (l)
                elif "(get-model)" not in l:
                    new.write (l)
            new.write ("(get-model)\n")
        

    def buildCMDList (self,smtfilepath):
        return [self._path,"--lang","smt2","-m","--no-interactive-prompt","--strings-exp","--produce-models",smtfilepath]
    
    
