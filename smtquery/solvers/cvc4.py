import smtquery.solvers.solver as solver
import subprocess
import re

class CVC4(solver.Solver):
    def __init__(self,binarypath):
        super().__init__(binarypath)
        self._path = binarypath
        
    def getVersion (self):
        return subprocess.check_output ([self._path,"--version"])

    def getName (self):
        return "CVC4"
    
    def preprocessSMTFile  (self, origsmt, newsmt):
        #set logic present?
        setLogicPresent = False
        with open(origsmt,'r') as flc:
            for l in flc:
                if not l.startswith(";") and '(set-logic' in l:
                    setLogicPresent = True

        with open(origsmt,'r') as orig, open(newsmt,'w') as new:
            if not setLogicPresent:
                new.write("(set-logic QF_SLIA)\n")
            for l in orig:
                # remove annotations
                for exp in ["\(get-model\)","\(check-sat\)","\(exit\)","\(set-info :status sat\)","\(set-info :status unsat\)"]:
                    l = re.sub(exp, '', l)

                # change logic if needed
                if "(set-logic" in l:
                    l = re.sub('\(set-logic.*?\)', '(set-logic QF_SLIA)', l)
                new.write(l)
            new.write("\n(check-sat)\n(get-model)")        

    def buildCMDList (self,smtfilepath):
        return [self._path,"--lang","smtlib2.5","-m","--no-interactive-prompt","--strings-exp","--dump-models",smtfilepath]