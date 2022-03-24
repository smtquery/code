import math

import smtquery.ui
import smtquery.storage.smt.fs
import smtquery.intel
from smtquery.smtcon.smt2expr import Z3SMTtoSExpr
from smtquery.smtcon.expr import *


class RenameVariables:

    @staticmethod
    def getName():
        return 'RenameVariables'

    rename_dict = {Sort.String: 'str', Sort.Bool: 'bool', Sort.Int: 'int', Sort.RegEx: 'rgx'}

    def __call__(self, smtfile, rename_dict=None):
        if rename_dict:
            self.rename_dict.update(rename_dict)
        # nVar = {k:len(v) for k, v in smtfile.Probes.getIntel()['variables'].items()}

        new_ast = ASTRef()
        # ast = smtfile.Probes._get()
        ast = Z3SMTtoSExpr().getAST(smtfile._filepath)

        # issue: renaming is not invariant between multiple runs
        self.subst_dict = {name: f'{self.rename_dict[sort]}{str(i+1).zfill(math.floor(math.log(len(names), 10))+1)}'
                           for sort, names in ast.get_intel()['variables'].items() for i, name in enumerate(names)}

        for ass in ast:
            new_ast.add_node(self._substitute_in_node(ass))

        print(new_ast)


    def _substitute_in_node(self, node):
        if node.kind() == Kind.VARIABLE:
            node.vDecl = self.subst_dict[node.vDecl]
        else:
            node.vChildren = list(map(self._substitute_in_node, node.children()))
        return node


def PullExtractor():
    return [RenameVariables]