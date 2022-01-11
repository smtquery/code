import smtquery.smtcon.smt2expr
import smtquery.smtcon.exprfun
import smtquery.intel.plugins.probes
from smtquery.smtcon.expr import Kind
import smtquery.qlang.predicates
import tempfile
import z3
import graphviz 
import os
import importlib
from functools import partial


class Plugin:
    def getIntel (self, smtfile):
        return None

    def predicates (self):
        return {

    }

    def getName (self):
        return "Dummy"

    def getVersion (self):
        return "0.0.1"
    
    
    
    
plugins = {}

def registerPlugin (name,create):
    plugins[name] = create

def searchPlugins ():
    root = os.path.split(os.path.abspath(__file__))[0]
    for f in os.listdir (root):
        if os.path.isfile (os.path.join (root,f)):
            if f.endswith (".py") and f != "__init__.py":
                mod = importlib.import_module (f"smtquery.intel.plugins.{f.replace('.py','')}")
                plug = mod.makePlugin ()
                registerPlugin (plug.getName (),plug)
            
searchPlugins ()
        
