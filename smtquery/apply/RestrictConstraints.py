import smtquery.ui

from smtquery.smtcon.expr import *
from smtquery.smtcon.exprfun import *


class RestrictConstraints:
    @staticmethod
    def getName ():
        return "RestrictConstraints"

    def __call__  (self,smtfile):
        
        collect_kinds = [Kind.LENGTH_CONSTRAINT,Kind.WEQ] #[Kind.REGEX_CONSTRAINT,Kind.WEQ]
        new_ast = ASTRef()
        ast = smtfile.Probes._get()

        for ass in ast:
            new_ass_list = []
            if ass.kind() == Kind.WEQ and ass.kind() in collect_kinds:
                new_ass_list = self._processWEQ(ass)
            elif ass.kind() == Kind.REGEX_CONSTRAINT and ass.kind() in collect_kinds:
                new_ass_list = self._processRegEx(ass)
            elif ass.kind() == Kind.LENGTH_CONSTRAINT and ass.kind() in collect_kinds:
                new_ass_list = self._processLength(ass)
            elif ass.kind() == Kind.OTHER and ass.sort() == Sort.Bool:
                new_ass_list = self._processBool(ass,collect_kinds)

            if len(new_ass_list) == 1:
                new_ast.add_node(new_ass_list[0])

        print(new_ast)

        ## create new smtfile out of new_ast!

        return smtfile
    
    def _processWEQ(self,expr):
        if set(expr.intel["has"].keys()).issubset({Kind.CONSTANT,Kind.VARIABLE,Kind.WEQ,Kind.OTHER}):
            expr.reset_intel()
            return [expr]
        return []

    def _processRegEx(self,expr):
        return [expr]

    def _processLength(self,expr):
        if set(expr.intel["has"].keys()).issubset({Kind.CONSTANT,Kind.VARIABLE,Kind.LENGTH_CONSTRAINT,Kind.OTHER}):
            expr.reset_intel()
            return [expr]
        return []

    def _processBool(self,expr,collect_kinds):
        new_kids = []
        for c in expr.children():
            if c.kind() == Kind.WEQ and c.kind() in collect_kinds:
                kid = self._processWEQ(c)
                if len(kid) >= 1:
                    new_kids+=kid
            elif c.kind() == Kind.REGEX_CONSTRAINT and c.kind() in collect_kinds:
                kid = self._processRegEx(c)
                if len(kid) >= 1:
                    new_kids+=kid
            elif c.kind() == Kind.LENGTH_CONSTRAINT and c.kind() in collect_kinds:
                kid = self._processLength(c)
                if len(kid) >= 1:
                    new_kids+=kid 
            elif c.kind() == Kind.OTHER and c.sort() == Sort.Bool:
                new_kids+=self._processBool(c,collect_kinds)         
        if new_kids == None or len(new_kids) == 0:
            return []
        elif len(new_kids) == 1:
            return [new_kids[0]]
        else:
            expr.vChildren = new_kids
            return [expr]
        



def PullExtractor():
    return [RestrictConstraints]
