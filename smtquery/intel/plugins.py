import smtquery.smtcon.smt2expr
import smtquery.smtcon.exprfun
from smtquery.smtcon.expr import Kind
import smtquery.qlang.predicates
import tempfile
import z3
from functools import partial

class Plugin:
    def __init__(self,name,version):
        self._name = name
        self._version = version

    def getName (self):
        return self._name
    

    def getVersion (self):
        return self._version


    def getIntel (self, smtfile):
        return None

    def predicates (self):
        return {

    }
    

class Probing(Plugin):
    def __init__(self):
        super().__init__ ("Probes","0.0.1")
        self._smtprobe = smtquery.smtcon.smt2expr.Z3SMTtoSExpr ()
        
    def getIntel (self, smtfile):
        with tempfile.TemporaryDirectory () as tmpdir:
            filepath = smtfile.copyOutSMTFile (tmpdir)
            pr = self._smtprobe.getAST (filepath)

            # demo
            pr.add_intel_with_function(smtquery.smtcon.exprfun.HasAtom().apply,smtquery.smtcon.exprfun.HasAtom().merge,dict(),"has")

            # plot test
            import graphviz 
            dot = graphviz.Digraph('G', format='pdf')
            pr.add_intel_with_function(smtquery.smtcon.exprfun.Plot().apply,smtquery.smtcon.exprfun.Plot().merge,{"dot" : dot, "succ" : [], "colours" : dict()},"plot")
            dot.render("test")

            return pr

    def predicates (self):
        return {
            "hasWEQ" : partial(hasKind,Kind.WEQ),
            "hasLinears" : partial(hasKind,Kind.LENGTH_CONSTRAINT),
            "hasRegex" : partial(hasKind,Kind.REGEX_CONSTRAINT)
        }

def hasKind(kind,smtfile):
    if kind in smtfile.Probes.get_intel()["has"]:
        return smtquery.qlang.predicates.Trool.TT
    else:
        return smtquery.qlang.predicates.Trool.FF 

###### OLD STUFF!
class ProbeSMTFiles(Plugin):
    hofunc = ["At","str.substr","PrefixOf","SuffixOf","Contains","IndexOf","Replace","IntToStr","StrToInt"]
    def __init__(self):
        super().__init__("SMTProbe","0.1")
        self.s = z3.Solver()

    def getZ3AST(self,instance_path):
        return z3.parse_smt2_file(instance_path)

    def _mergeData(self,d1,d2):
        for k in set(d1.keys()).union(set(d2.keys())):
            if k in d1 and k in d2:
                if isinstance(d1[k],int): 
                    d1[k] = d1[k]+d2[k]
                else:
                    d1[k] = self._mergeData(d1[k],d2[k])
            elif k in d2:
                d1[k] = d2[k]
        return d1
    
    def traverseAst(self,ast):
        data = {"variables": dict(), "weq":0,"length":0,"regex":0,"hof":{f : 0 for f in self.hofunc}}
        if type(ast) in [z3.z3.AstVector]:
            for x in ast:
                data = self._mergeData(data,self.traverseAst(x))
        else:
            children = ast.children()
            if len(children) == 0:
            #    if str(ast.sort()) == "String":
            #        if not ast.is_string_value():
            #            x = str(ast)
            #            if x not in data["variables"]:
            #                data["variables"][x] = 0
            #            data["variables"][x]+=1
                return data
            op = ast.decl()
            if str(op) == "InRe":
                data["regex"]+=1
            elif str(op) in self.hofunc:
                data["hof"][str(op)]+=1
            if type(ast) == z3.z3.BoolRef and len(children) == 2 and str(children[0].sort()) == "String" and children[0].sort() == children[1].sort():
                data["weq"]+=1
            elif type(ast) == z3.z3.BoolRef and len(children) == 2 and str(children[0].sort()) == "Int" and children[0].sort() == children[1].sort():
                data["length"]+=1

            for x in children:
                data = self._mergeData(data,self.traverseAst(x))
        return data

    
    
        
    def needsDB (self):
        return True
    
    def processInstance(self,path):
        instancedata = self.traverseAst(self.getZ3AST(path))
        dbvalues = {}
        for k in instancedata.keys():
            if isinstance(instancedata[k],int):
                dbvalues[k] = instancedata[k]
            elif isinstance(instancedata[k],dict):
                for kk in instancedata[k].keys():
                    dbvalues[kk] = instancedata[k][kk]
        return dbvalues


def hasWordEquations (smtfile):
    if smtfile.Probes.get_intel()["has"][Kind.WEQ] > 0:
        return smtquery.qlang.predicates.Trool.TT
    else:
        return smtquery.qlang.predicates.Trool.FF


    
class OldProbing(Plugin):
    def __init__(self):
        super().__init__ ("OldProbes","0.0.1")
        self._smtprobe = ProbeSMTFiles ()
        
    def getIntel (self, smtfile):
        with tempfile.TemporaryDirectory () as tmpdir:
            filepath = smtfile.copyOutSMTFile (tmpdir)
            pr = self._smtprobe.processInstance (filepath)
            return pr