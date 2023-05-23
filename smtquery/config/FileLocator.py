
import os

class FileLocator:
    def __init__(self,paths = []):
        self._roots = paths

    def findFile (self,name):
        
        for p in self._roots:
            path = os.path.join (p,name)
            if os.path.exists (path):
                return path
        return None
