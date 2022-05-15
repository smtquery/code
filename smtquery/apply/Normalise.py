from smtquery.smtcon.expr import ASTRef
import smtquery.ui
import smtquery.storage.smt.fs
import smtquery.intel


class DisjoinConstraints:
    output_folder = 'output/disjoin_constraints'
    root = '.'

    @staticmethod
    def getName():
        return 'DisjoinConstraints'

    def __call__(self, smtfile):
        new_ast = ASTRef()
        ast = smtfile.Probes._get()

        for ass in ast:
            for expr in self._extract_constraints(ass):
                new_ast.add_node(expr)

        with smtquery.ui.output.makeFile(self._getOutputFilePath(smtfile)) as handle:
            handle.write(str(new_ast))
        new_smtfile = smtquery.storage.smt.fs.SMTFile(smtfile.getName(),self.root+"/"+self._getOutputFilePath(smtfile))
        smtquery.intel.intels.getIntel(new_smtfile)
        return new_smtfile

    def _getOutputFilePath(self,smtfile):
        return self.output_folder+''.join(f"/{f}" for f in smtfile.getName().split(":"))

    def _extract_constraints(self, expr):
        '''takes and-concatenations of constraints and returns them in a list'''
        new_expr = []
        q = [expr]
        while q:
            cur = q.pop()
            if cur.decl() == 'and':
                q.extend(cur.children())
            else:
                new_expr.append(cur)

        return new_expr


class SortConstraints:
    output_folder = 'output/sort_constraints'
    root = '.'

    @staticmethod
    def getName():
        return 'SortConstraints'

    def __call__(self, smtfile):
        new_ast = ASTRef()
        ast = smtfile.Probes._get()
        for i, _ in sorted(enumerate([str(x) for x in ast]), key=lambda x: x[1]):
            new_ast.add_node(ast[i])

        with smtquery.ui.output.makeFile(self._getOutputFilePath(smtfile)) as handle:
            handle.write(str(new_ast))
        new_smtfile = smtquery.storage.smt.fs.SMTFile(smtfile.getName(),self.root+"/"+self._getOutputFilePath(smtfile))
        smtquery.intel.intels.getIntel(new_smtfile)
        return new_smtfile

    def _getOutputFilePath(self,smtfile):
        return self.output_folder+''.join(f"/{f}" for f in smtfile.getName().split(":"))


def PullExtractor():
    return [DisjoinConstraints, SortConstraints]