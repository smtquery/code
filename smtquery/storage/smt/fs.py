import os
import hashlib
import shutil

class SMTFile:
    def __init__(self,name,filepath):
        assert (os.path.exists(filepath))
        self._name = name
        self._filepath = filepath
        
        
    def SMTString (self):
        with open(self._filepath,'r') as ff:
            return ff.read ()
        
    
    def hashContent (self):
        with open(self._filepath,'r') as ff:
            return hashlib.sha256 (ff.read().encode ()).hexdigest ()

    def copyOutSMTFile (self,directory):
        name = os.path.split (self._filepath)[1]
        shutil.copyfile (self._filepath,os.path.join (directory,name))
        return os.path.join (directory,name)

    def getName (self):
        return self._name
    
class SMTTrack:
    def __init__(self,name, directory):
        self._name = name
        assert (os.path.exists(directory))
        self._directory = directory

    def filesInTrack (self):
        for root, dirs,files in os.walk (self._directory):
            for f in files:
                if f.endswith (".smt") or f.endswith (".smt2") or f.endswith (".smt25"):
                    yield SMTFile (f"{self._name}:{f}",os.path.join (root,f))
    

    def searchFile (self,searchname):
        if searchname.endswith (".smt") or searchname.endswith (".smt2") or searchname.endswith (".smt25"):
            name = searchname
        else:
            name = f"{searchname}.smt"
        if os.path.exists (os.path.join (self._directory,name)):
            return SMTFile (f"{self._name}:{name}",os.path.join (self._directory,name))
        else:
            return None
        

class SMTStorage:
    def __init__(self,directory):
        self._directory = directory
        assert(os.path.exists (self._directory))
        
        
    def tracksInStore (self):
        for root, dirs,files in os.walk (self._directory):
            if len(files) > 0:
                d = os.path.split (root)[1]
                yield SMTTrack (f"{d}",root)
                
    def searchForTrack (self,name):
        if os.path.exists (os.path.join (self._directory,name)):
            return SMTTrack (name,os.path.join (self._directory,name))
        else:
            return None
    
    
            
