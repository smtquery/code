from smtquery.smtcon.expr import *
from smtquery.smtcon.exprfun import *

class SMTtoSExpr:
    def __init__(self):
        pass


######

#test

class Reference:
    def __init__(self, val):
        self._value = val # just refers to val, no copy

    def get(self):
        return self._value

    def set(self, val):
        self._value = val

###

class ParserError(Exception):
    def __init__(self,file_path,msg):
        self.msg = msg
        self.file_path = file_path
    def __str__(self):
        return f"Error while parsing {self.file_path}: {self.msg}"


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

    def getZ3AST(self,file_path):
        try:
            ctx = z3.Context()
            return z3.parse_smt2_file(file_path,ctx=ctx)
        except Exception as e:
            raise ParserError(file_path,f"{e}")

    def getZ3ASTFromText(self,text):
        return z3.parse_smt2_string(text)

    def getASTFromText(self,text):
        return self._buildAST(self.getZ3ASTFromText(text))   

    def getAST(self,file_path):
        return self._buildAST(self.getZ3AST(file_path))

    def _buildAST(self,z3ast):
        ast = ASTRef()
        node_id = [0] # list to pass it as reference
        if type(z3ast) in [z3.z3.AstVector]:
            for e in z3ast:
                ast.add_node(self.translateExpr(e,node_id))
        return ast

    def _extractOpName(self,op):
        return str(op.sexpr()).split(" ")[1]

    # HOL functions
    hofunc = ["At","str.substr","PrefixOf","SuffixOf","Contains","IndexOf","Replace","IntToStr","StrToInt"]
    def _determineKind(self,expr,is_variable,is_const):
        if is_variable:
            return Kind.VARIABLE
        if is_const:
            return Kind.CONSTANT

        children = expr.children()
        if str(expr.decl()) in self.hofunc:
            return Kind.HOL_FUNCTION
        elif str(expr.decl()) == "InRe":
            return Kind.REGEX_CONSTRAINT
        elif type(expr) == z3.z3.BoolRef and len(children) == 2 and str(children[0].sort()) == "String" and children[0].sort() == children[1].sort():
            return Kind.WEQ
        elif type(expr) == z3.z3.BoolRef and len(children) == 2 and str(children[0].sort()) == "Int" and children[0].sort() == children[1].sort():
            return Kind.LENGTH_CONSTRAINT
        else:
            return Kind.OTHER

    def translateExpr(self,expr,node_id_ref):
        node_id = node_id_ref[0]
        passed = dict()
        tree = dict()

        t_expr = self._prepareExpr(expr,node_id)

        node_id+=1
        root = node_id
        waiting = [(Reference(t_expr),expr.children(),node_id)]

        while len(waiting) > 0:
            e_ref,children,t_id = waiting.pop(0)
            e = e_ref.get()

            for c in children:
                node_id+=1
                t_c = self._prepareExpr(c,node_id)
                e.vChildren+=[t_c]
                
                c_children = c.children()
                if len(c_children) > 0:
                    waiting+=[(Reference(t_c),c_children,node_id)]
                    #tree[t_id]+=[node_id]
            e_ref.set(e)

        #print(t_expr)

        return t_expr
        """
        node_id = node_id_ref[0]
        passed = dict()
        tree = dict()


        node_id+=1
        root = node_id
        waiting = [(expr,node_id)]


        while len(waiting) > 0:
            e,t_id = waiting.pop(0)
            tree[t_id] = []
            passed[t_id] = self._prepareExpr(e,t_id)
            for c in e.children():
                node_id+=1
                waiting+=[(c,node_id)]
                tree[t_id]+=[node_id]



        # rebuild tree
        node_id_ref = [node_id]
        processed = set({root})
        set(tree.keys())

        while processed != set(tree.keys()):
            for i in set(j for j in tree.keys() if len(tree[j]) == 0 and j not in processed):
                print(i)
                processed.add(i)
                for ii in set(j for j in tree.keys() if i in tree[j]):
                    tree[ii].remove(i)
                    passed[ii].vChildren+=[passed[i]]
        
        return passed[root]
        """




    def _prepareExpr(self,expr,node_id):
        sort = self.getSort(expr.sort())
        is_variable = z3.is_const(expr) and expr.decl().kind() == z3.Z3_OP_UNINTERPRETED
        is_const = not is_variable and len(expr.children()) == 0
        op = self._extractOpName(expr.decl())
        kind = self._determineKind(expr,is_variable,is_const)
        empty_children = []

        if is_const:
            params = [expr.sexpr()]
        else:
            params = expr.params()

        if type(expr) == z3.z3.SeqRef:
            return StringExpr(empty_children,params,str(op),kind,dict(),node_id)  
        elif type(expr) == z3.z3.BoolRef:
            return BoolExpr(empty_children,params,str(op),kind,dict(),node_id)
        elif type(expr) == z3.z3.ReRef:
            return ReExpr(empty_children,params,str(op),kind,dict(),node_id)
        elif type(expr) == z3.z3.ArithRef:
            return IntExpr(empty_children,params,str(op),kind,dict(),node_id)
        elif type(expr) == z3.z3.IntNumRef:
            return IntExpr(empty_children,params,str(op),kind,dict(),node_id)


        # Fall back
        return ExprRef(empty_children,[],str(op),kind,dict(),node_id) 



    def translateExprRec(self,expr,node_id_ref):
        sort = self.getSort(expr.sort())
        children = [self.translateExprRec(c,node_id_ref) for c in expr.children()]
        node_id_ref[0] = node_id_ref[0]+1
        is_variable = z3.is_const(expr) and expr.decl().kind() == z3.Z3_OP_UNINTERPRETED
        is_const = not is_variable and len(children) == 0
        op = self._extractOpName(expr.decl())
        kind = self._determineKind(expr,is_variable,is_const)
        
        if is_const:
            params = [expr.sexpr()]
        else:
            params = expr.params()

        if type(expr) == z3.z3.SeqRef:
            return StringExpr(children,params,str(op),kind,dict(),node_id_ref[0])  
        elif type(expr) == z3.z3.BoolRef:
            return BoolExpr(children,params,str(op),kind,dict(),node_id_ref[0])
        elif type(expr) == z3.z3.ReRef:
            return ReExpr(children,params,str(op),kind,dict(),node_id_ref[0])
        elif type(expr) == z3.z3.ArithRef:
            return IntExpr(children,params,str(op),kind,dict(),node_id_ref[0])
        elif type(expr) == z3.z3.IntNumRef:
            return IntExpr(children,params,str(op),kind,dict(),node_id_ref[0])


        # Fall back
        return ExprRef(children,[],str(op),kind,dict(),node_id_ref[0]) 
