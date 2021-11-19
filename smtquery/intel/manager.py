class Manager:
    def __init__(self,plugins = None):
        self._plugins = plugins or {}

    def addPlugin (self,p):
        self._plugins[p.getName()] = p
        
    def getIntel (self,smtfile):
        for s,p in self._plugins.items():
            setattr(smtfile,s,p.getIntel (smtfile))
            
        return smtfile

    def predicates (self):
        res = {}
        for p in self._plugins.values():
            res.update(p.predicates ())
        return res
