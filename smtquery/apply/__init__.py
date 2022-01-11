import os
import importlib

applys = {}

def registerPlugin (name,create):
    applys[name] = create

def searchPlugins ():
    root = os.path.split(os.path.abspath(__file__))[0]
    for f in os.listdir (root):
        if os.path.isfile (os.path.join (root,f)):
            if f.endswith (".py") and f != "__init__.py":
                mod = importlib.import_module (f"smtquery.apply.{f.replace('.py','')}")
                for p in mod.PullExtractor ():
                    registerPlugin (p.getName (),p ())
            
searchPlugins ()
