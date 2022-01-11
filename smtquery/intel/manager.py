class Proxy:
    def __init__ (self,cls,params):
        self._obj = None
        self._cls = cls
        self._params = params

    def _get (self):
        if not self._obj:
            self._obj = self._cls(*self._params)
        return self._obj
    
    def __getattr__(self,name):
        return self._get().__getattr__(name)

    def __getitem__(self, key):
        return self._get().__getitem__(key)
    
class Manager:
    def __init__(self,plugins = None):
        print ("New Manager")
        self._plugins = plugins or {}

    def addPlugin (self,p):
        self._plugins[p.getName()] = p
        
    def getIntel (self,smtfile):
        for s,p in self._plugins.items():
            setattr(smtfile,s,Proxy(p.getIntel,[smtfile]))
            
        return smtfile

    def predicates (self):
        res = {}
        for p in self._plugins.values():
            res.update(p.predicates ())
        
        return res
