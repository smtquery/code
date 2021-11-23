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

class HasAtom(ExprFun):
    def __init__(self):
        super().__init__ ("HasAtom","0.0.1")
        
    def apply (self, expr, data):
        if expr.kind() not in data:
            data[expr.kind()] = 0
        data[expr.kind()]+=1
        return data

    def merge(self, expr, d1,d2):
        for k in set(d1.keys()).union(set(d2.keys())):
            if k in d1 and k in d2:
                d1[k] = d1[k]+d2[k]
            elif k in d2:
                d1[k] = d2[k]
        return d1

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

    def merge(self,expr,d1,d2):
        for k in set(d1.keys()).union(set(d2.keys())):
            if k in d1 and k in d2:
                if isinstance(d1[k],int): 
                    d1[k] = d1[k]+d2[k]
                else:
                    d1[k] = merge_f(d1[k],d2[k],expr)
            elif k in d2:
                d1[k] = d2[k]
        return d1

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

    def merge(self,expr,d1,d2):
        if expr.id() != d2['succ'][0] and expr.id() != 0: # skip root node
            d1["dot"].edge(f"{expr.id()}", f"{d2['succ'][0]}",penwidth="0.5",arrowhead="none")  
        d1["succ"] = []
        return d1

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