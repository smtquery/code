
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
        print (id)
        for k in instancedata.keys():
            if isinstance(instancedata[k],int):
                dbvalues[k] = instancedata[k]
            elif isinstance(instancedata[k],dict):
                for kk in instancedata[k].keys():
                    dbvalues[kk] = instancedata[k][kk]
        conn = self._engine.connect ()
        conn.execute (self._instance_table.insert ().values ([dbvalues]))
    
