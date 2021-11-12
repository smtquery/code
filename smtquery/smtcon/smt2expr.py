from expr import *

class SMTtoSExpr:
    def __init__(self):
        pass


######


import z3
class Z3SMTtoSExpr(SMTtoSExpr):

    def getSort(self,sort):
        if str(sort) == "Bool":
            return Sort.Bool
        elif str(sort) == "String":
            return Sort.Bool
        elif str(sort) == "Int":
            return Sort.Int
        elif str(sort) == "ReSort(String)":
            return Sort.RegEx
        return None

    def getAST(self,file_path):
        return z3.parse_smt2_file(file_path)

    def getSExprList(self,file_path):
        ast = self.getAST(file_path)
        l = []
        if type(ast) in [z3.z3.AstVector]:
            l = [self.translateExpr(e) for e in ast]
        return l

    def _extractOpName(self,op):
        return str(op.sexpr()).split(" ")[1]


    def translateExpr(self,expr):
        sort = self.getSort(expr.sort())
        children = [self.translateExpr(c) for c in expr.children()]
        is_variable = z3.is_const(expr) and expr.decl().kind() == z3.Z3_OP_UNINTERPRETED
        is_const = not is_variable and len(children) == 0
        op = self._extractOpName(expr.decl())
        
        if is_const:
            params = [expr.sexpr()]
        else:
            params = expr.params()

        if type(expr) == z3.z3.SeqRef:
            return StringExpr(children,params,str(op),is_variable)  
        elif type(expr) == z3.z3.BoolRef:
            return BoolExpr(children,params,str(op),is_variable)
        elif type(expr) == z3.z3.ReRef:
            return ReExpr(children,params,str(op),is_variable)
        elif type(expr) == z3.z3.ArithRef:
            return IntExpr(children,params,str(op),is_variable)
        elif type(expr) == z3.z3.IntNumRef:
            return IntExpr(children,params,str(op),is_variable)


        # Fall back
        return ExprRef(children,[],str(op),is_variable) 