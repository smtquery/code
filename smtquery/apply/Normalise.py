from smtquery.smtcon.expr import ASTRef
from smtquery.smtcon.smt2expr import Z3SMTtoSExpr


class DisjoinConstraints:

    @staticmethod
    def getName():
        return 'DisjoinConstraints'

    def __call__(self, smtfile):
        new_ast = ASTRef()
        # ast = smtfile.Probes._get()
        ast = Z3SMTtoSExpr().getAST(smtfile._filepath)

        for ass in ast:
            for expr in self._extract_constraints(ass):
                new_ast.add_node(expr)

        print(new_ast)


    def _extract_constraints(self, expr):
        new_expr = []
        q = [expr]
        while q:
            cur = q.pop()
            if cur.decl() == 'and':
                q.extend(cur.children())
            else:
                new_expr.append(cur)

        return new_expr


class NormaliseConstraints:

    @staticmethod
    def getName():
        return 'NormaliseConstraints'

    def __call__(self, smtfile):
        new_ast = ASTRef()
        # ast = smtfile.Probes._get()
        ast = Z3SMTtoSExpr().getAST(smtfile._filepath)

        for ass in ast:
            print(ass.children())


class SortConstraints:

    @staticmethod
    def getName():
        return 'SortConstraints'

    def __call__(self, smtfile):
        new_ast = ASTRef()
        # ast = smtfile.Probes._get()
        ast = Z3SMTtoSExpr().getAST(smtfile._filepath)
        for i, _ in sorted(enumerate([str(x) for x in ast]), key=lambda x: x[1]):
            new_ast.add_node(ast[i])

        print(new_ast)


def PullExtractor():
    return [NormaliseConstraints, DisjoinConstraints, SortConstraints]