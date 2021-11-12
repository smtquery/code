from enum import Enum

class Sort(Enum):
    String = 1
    Bool = 2
    Int = 3
    RegEx = 4

class Kind(Enum):
    Variable = 1
    Constant = 2
    Other = 3

class ExprRef:
    vChildren = []
    vParams = []
    vDecl = None
    vSort = None
    isVariable = False

    # additional data
    intel = None

    def __init__(self,children,params,decl,isVariable,intel=dict()):
        self.vChildren = children
        self.vParams = params
        self.vDecl = decl
        self.isVariable = isVariable
        self.intel = intel

    def children(self):
        return self.vChildren

    def decl(self):
        return self.vDecl

    def params(self):
        return self.vParams

    def sort(self):
        return self.vSort

    def is_const(self):
        return not self.isVariable and len(self.vChildren) == 0

    def is_variable(self):
        return self.isVariable

    # f : Expr x Value -> Value
    def add_intel_with_function(self,f,neutral=0,key="test"):
        if key in self.intel:
            value = self.intel[key]
        else:
            value = neutral

        self.intel[key] = f(self,neutral)

        # aquire values from children
        for c in self.children():
            c.add_intel_with_function(f,neutral,key)

        ### BUG WITHIN THE MERGING --- CHECK THIS AGAIN!


        # merge the intel
        #self._merge_intel_from_children()

    def get_intel(self):
        return self.intel

    def _merge_intel_from_children(self):
        this_intel = self.get_intel()
        for c in self.children():
            c._merge_intel_from_children()
            other_intel = c.get_intel()
            print(other_intel)
            this_intel = self._merge_dictionaries(this_intel,other_intel)
        self.intel = this_intel

    def _merge_dictionaries(self,d1,d2):
        for k in set(d1.keys()).union(set(d2.keys())):
            if k in d1 and k in d2:
                if isinstance(d1[k],int): 
                    d1[k] = d1[k]+d2[k]
                else:
                    d1[k] = self._merge_dictionaries(d1[k],d2[k])
            elif k in d2:
                d1[k] = d2[k]
        return d1

    def __repr__(self):
        if self.is_const():
            return ''.join(f"{s}" for s in self.vParams)
        else:
            if len(self.vChildren) == 0:
                return f"{self.vDecl}"
            if len(self.vParams) > 0:
                r_str=f"((_ {self.vDecl}"+''.join([f" {p}" for p in self.vParams])+") "
            else:
                r_str = f"({self.vDecl} "
            r_str+=''.join([f"{c} " for c in self.vChildren])[:-1]
            r_str+=")"
            return r_str

    def __eq__(self,other):
        return self.vChildren == other.vChildren and self.vParams == other.vParams and self.vDecl == other.vDecl and self.vSort == other.vSort

class StringExpr(ExprRef):
    vSort = Sort.String

class BoolExpr(ExprRef):
    vSort = Sort.Bool

class ReExpr(ExprRef):
    vSort = Sort.RegEx

class IntExpr(ExprRef):
    vSort = Sort.Int
