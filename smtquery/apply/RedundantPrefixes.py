from smtquery.smtcon.expr import ASTRef, BoolExpr
import smtquery.ui
import smtquery.storage.smt.fs
import smtquery.intel
from smtquery.smtcon.smt2expr import Z3SMTtoSExpr


class EqualsTrue:
    output_folder = 'output/prefix_true'
    root = '.'

    @staticmethod
    def getName():
        return 'EqualsTrue'

    def __call__(self, smtfile):
        new_ast = ASTRef()
        ast = smtfile.Probes._get()

        for ass in ast:
            while ass.decl() == '=' and str(ass.children()[0]) == 'true':
                ass = ass.children()[1]
            new_ast.add_node(ass)

        with smtquery.ui.output.makeFile(self._getOutputFilePath(smtfile)) as handle:
            handle.write(str(new_ast))
        new_smtfile = smtquery.storage.smt.fs.SMTFile(smtfile.getName(),self.root+"/"+self._getOutputFilePath(smtfile))
        smtquery.intel.intels.getIntel(new_smtfile)
        return new_smtfile

    def _getOutputFilePath(self,smtfile):
        return self.output_folder+''.join(f"/{f}" for f in smtfile.getName().split(":"))


class ReduceNegations:
    output_folder = 'output/prefix_negations'
    root = '.'

    @staticmethod
    def getName():
        return 'ReduceNegations'

    def __call__(self, smtfile):
        new_ast = ASTRef()
        ast = smtfile.Probes._get()

        for ass in ast:
            while ass.decl() == 'not' and isinstance(ass.children()[0], BoolExpr) and ass.children()[0].decl() == 'not':
                ass = ass.children()[0].children()[0]
            new_ast.add_node(ass)

        with smtquery.ui.output.makeFile(self._getOutputFilePath(smtfile)) as handle:
            handle.write(str(new_ast))
        new_smtfile = smtquery.storage.smt.fs.SMTFile(smtfile.getName(),self.root+"/"+self._getOutputFilePath(smtfile))
        smtquery.intel.intels.getIntel(new_smtfile)
        return new_smtfile


    def _getOutputFilePath(self,smtfile):
        return self.output_folder+''.join(f"/{f}" for f in smtfile.getName().split(":"))


def PullExtractor():
    return [EqualsTrue, ReduceNegations]
