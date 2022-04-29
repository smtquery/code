from smtquery.smtcon.expr import ASTRef, BoolExpr
from smtquery.smtcon.smt2expr import Z3SMTtoSExpr


class EqualsTrue:

    @staticmethod
    def getName():
        return 'EqualsTrue'

    def __call__(self, smtfile):
        new_ast = ASTRef()
        # ast = smtfile.Probes._get()
        ast = Z3SMTtoSExpr().getAST(smtfile._filepath)

        for ass in ast:
            while ass.decl() == '=' and str(ass.children()[0]) == 'true':
                ass = ass.children()[1]
            new_ast.add_node(ass)


class ReduceNegations:

    @staticmethod
    def getName():
        return 'ReduceNegations'

    def __call__(self, smtfile):
        new_ast = ASTRef()
        # ast = smtfile.Probes._get()
        ast = Z3SMTtoSExpr().getAST(smtfile._filepath)

        for ass in ast:
            while ass.decl() == 'not' and isinstance(ass.children()[0], BoolExpr) and ass.children()[0].decl() == 'not':
                ass = ass.children()[0].children()[0]
            new_ast.add_node(ass)

        print(new_ast)


def PullExtractor():
    return [EqualsTrue, ReduceNegations]
