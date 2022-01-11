import os

from smtquery.ui.progress import Progresser as Progresss
from smtquery.ui.progress import Message as Messager


class Outputter:
    def __init__(self,root):
        self._root = root

    def makeSubOutput (self,name):
        path  = os.path.join (self._root,name)
        os.makedirs (path,exist_ok = True)
        return OutputLocator (path)

    def makeFile (self,name):
        return open (os.path.join (self._root,name,'w'))

    def makeBinaryFile (self,name):
        return open (os.path.join (self._root,name,'bw'))

    def makeProgressor (self):
        return Progresss()
    
    def makePlainMessager (self):
        return Messager ()
    
output = Outputter (".")
