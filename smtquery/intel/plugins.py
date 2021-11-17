import smtquery.smtcon.smt2expr
import tempfile

class Plugins:
    def __init__(self,name,version):
        self._name = name
        self._version = version

    def getName (self):
        return self._name
    

    def getVersion (self):
        return self._version


    def getIntel (self, smtfile):
        return None
    

class Probing(Plugins):
    def __init__(self):
        super().__init__ ("Probes","0.0.1")
        self._smtprobe = smtquery.smtcon.smt2expr.Z3SMTtoSExpr ()
        
    def getIntel (self, smtfile):
        with tempfile.TemporaryDirectory () as tmpdir:
            filepath = smtfile.copyOutSMTFile (tmpdir)
            pr = self._smtprobe.getAST (filepath)
            return pr
    
    
        
