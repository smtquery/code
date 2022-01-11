import hashlib
import math

from smtquery.smtcon.expr import *

class ExprFun:
    def __init__(self,name,version):
        self._name = name
        self._version = version
    def getName (self):
        return self._name
    def getVersion (self):
        return self._version
    def apply (self, expr, data):
        return None
    def merge(self, expr, data1, data2):
        return None


class AssertTrue(ExprFun):
    def __init__(self):
        super().__init__('AssertTrue', '0.0.1')

    def apply(self, expr, data):
        if isinstance(expr, BoolExpr) and ['true'] in [x.params() for x in expr.children()]:
            data += 1
        return data

    def merge(self, expr, data):
        return sum(data)


class TerminalLengths(ExprFun):
    def __init__(self):
        super().__init__('TerminalLengths', '0.0.1')

    def apply(self, expr, data):
        print(expr)
        if expr.is_const() and expr.sort() == Sort.String:
            l = len(expr.params()[0])-2
            data += [l]
        return data

    def merge(self, expr, data):
        d_new = []
        for d in data:
            d_new += d
        return d_new

class HashConstraints(ExprFun):
    def __init__(self):
        super().__init__('HashConstraints', '0.0.1')

    def apply(self, expr, data):
        if expr.kind() != Kind.CONSTANT and expr.kind() != Kind.VARIABLE:
            h = hashlib.md5(repr(expr).encode('utf-8')).hexdigest()
            print(expr, h)
            if h not in data:
                data[h] = 0
            data[h] += 1
        return data

    def merge(self, expr, data):
        d_new = dict()
        for d in data:
            for k, v in d.items():
                if k not in d_new:
                    d_new[k] = 0
                d_new[k] += v

        return d_new

class Bounded(ExprFun):
    def __init__(self):
        super().__init__('Bounded', '0.0.1')

    def apply(self, expr, data):
        # TODO !=
        if expr.kind() == Kind.WEQ:
            v, c = None, None
            for e in expr.children():
                if e.is_variable():
                    v = str(e)
                elif e.is_const():
                    c = len(str(e))-2
            if v and c:
                data.update({v: (c, c)})
        elif expr.kind() == Kind.LENGTH_CONSTRAINT:
            v, c = None, None
            for e in expr.children():
                if e.is_const():
                    c = int(str(e))
                elif e.kind() == Kind.OTHER:
                    v = str(e.children()[0])
            if v and c:
                if expr.decl() == '<':
                    data.update({v: (0, c-1)})
                elif expr.decl() == '>':
                    data.update({v: (c+1, float('inf'))})
                elif expr.decl() == '<=':
                    data.update({v: (0, c)})
                elif expr.decl() == '>=':
                    data.update({v: (c, float('inf'))})
                elif expr.decl() == '=':
                    data.update({v: (c, c)})
        return data

    def merge(self, expr, data):
        # TODO: merge constraints on equal variables
        d_new = dict()
        for d in data:
            for k in set(d_new.keys()).union(set(d.keys())):
                if k in d_new and k in d:
                    # merge
                    d_new[k] = (max(d_new[k][0], d[k][0]), min(d_new[k][1], d[k][1]))
                elif k in d:
                    d_new[k] = d[k]
        return d_new


class HasAtom(ExprFun):
    def __init__(self):
        super().__init__ ("HasAtom","0.0.1")
        
    def apply (self, expr, data):
        if expr.kind() not in data:
            data[expr.kind()] = 0
        data[expr.kind()]+=1
        return data

    def merge(self, expr, data):
        d_new = dict()
        for d in data:
            for k in set(d_new.keys()).union(set(d.keys())):
                if k in d_new and k in d:
                    d_new[k]+=d[k]
                elif k in d:
                    d_new[k] = d[k]
        return d_new

class VariableCount(ExprFun):
    def __init__(self):
        super().__init__ ("VariableCount","0.0.1")
        
    def apply (self, expr, data):
        if expr.is_variable():
            sort = expr.sort()
            decl = str(expr.decl())
            if sort not in data:
                data[sort] = dict()
            if decl not in data[sort]:
                data[sort][decl] = 0
            data[sort][decl]+=1
        return data

    def merge(self,expr,data):
        d_new = dict()
        for d in data:
            for t in set(d_new.keys()).union(set(d.keys())):
                if t not in d_new.keys():
                    d_new[t] = d[t]
                elif t in d.keys():
                    for v in set(d_new[t].keys()).union(set(d[t].keys())):
                        if v not in d_new[t]:
                            d_new[t][v] = 0
                        if v in d_new[t] and v in d[t]:
                            d_new[t][v]+=d[t][v]
        return d_new

class VariableCountPath(ExprFun):
    def __init__(self):
        super().__init__ ("VariablePath","0.0.1")
    
    # data = [dict(),...]
    def apply (self, expr, data):
        if expr.is_variable():
            sort = expr.sort()
            decl = str(expr.decl())
            if len(data) == 0:
                data+=[dict()]
            for d in data:
                if sort not in d:
                    d[sort] = dict()
                if decl not in d[sort]:
                    d[sort][decl] = 0
                d[sort][decl]+=1
        return data

    def merge(self,expr,data):
        ### branching for ite is missing!
        # we have to merge the first child with the second AND the third
        # but this function is called independently for each child
        if isinstance(expr,ExprRef) and expr.decl() == "ite":
            assert(len(data) == 3)
            d_cond = data.pop(0)
            d_ret = []
            for stmt in data:
                for dd in stmt:
                    for d in d_cond:
                        d_ret+=[self._mergeDicts(d,dd)]
            return d_ret

        if isinstance(expr,ExprRef) and expr.decl() == "or":
            return [d for path in data for d in path]

        d_ret = data.pop(0) if len(data) > 0 else dict()
        while len(data) > 0:
            d_tmp = []
            d_n = data.pop(0)
            if len(d_ret) == 0:
                d_tmp = d_n
            elif len(d_n) == 0:
                d_tmp = d_ret
            else:
                for d in d_ret:
                    for dd in d_n:
                        d_tmp+=[self._mergeDicts(d,dd)]
            d_ret = d_tmp
        return d_ret



        """data = []
        if len(data1) == 0:
            return data2
        elif len(data2) == 0:
            return data1
        for d1 in data1:
            for d2 in data2:
                data+=[self._mergeDicts(d1,d2)]
        return data
        """
    def _mergeDicts(self,d1,d2):
        r_data = dict()        
        for k in set(d1.keys()).union(set(d2.keys())):
            if k in d1 and k in d2:
                if isinstance(d1[k],int): 
                    r_data[k] = d1[k]+d2[k]
                else:
                    r_data[k] = self._mergeDicts(d1[k],d2[k])
            elif k in d2:
                r_data[k] = d2[k] if isinstance(d2[k],int) else d2[k].copy()
            elif k in d1: 
                r_data[k] = d1[k] if isinstance(d1[k],int) else d1[k].copy()
        return r_data


class Plot(ExprFun):
    def __init__(self):
        super().__init__ ("Plot","0.0.1")    

    # data = {"dot" : dot, succ : successor node ids, colours : label -> colour}
    def apply (self, expr, data):
        label = expr.decl()
        if expr.is_variable() or expr.is_const():
            label = f"{expr}"
        if label not in data["colours"]:
            data["colours"][label] = self._getNewColour([data["colours"][l] for l in data["colours"]])
        data["dot"].node(name=f"{expr.id()}", label=f"{label}", style='filled,rounded', shape="rectangle", color=f"{data['colours'][label][0]}", fontcolor=f"{data['colours'][label][1]}")
        data["succ"]=[expr.id()]
        return data

    def merge(self,expr,data):
        d_new = dict()
        for d in data:
            if len(d_new) == 0:
                d_new["dot"] = d["dot"]
                d_new["succ"] = []
                d_new["colours"] = d["colours"]

            if len(d['succ']) > 0 and expr.id() != d['succ'][0] and expr.id() != 0: # skip root node
                d_new["dot"].edge(f"{expr.id()}", f"{d['succ'][0]}",penwidth="0.5",arrowhead="none")  
        return d_new

    # auxilary functions
    def _colourGen(self):
        import random
        r = lambda: random.randint(0,255)
        c_r,c_g,c_b = r(),r(),r()
        colourGen = lambda : '#%02X%02X%02X' % (c_r,c_g,c_b)
        textColour = "#000000" if ((c_r * 0.299) + (c_g * 0.587) + (c_b * 0.114)) > 186 else "#FFFFFF"
        return (colourGen(),textColour)

    def _getNewColour(self,colours):
        while True:
            newColour = self._colourGen()
            if newColour not in colours:
                return newColour