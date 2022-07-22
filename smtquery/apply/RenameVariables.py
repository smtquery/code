import math

import smtquery.ui
import smtquery.storage.smt.fs
import smtquery.intel
from smtquery.smtcon.expr import *

from smtquery.intel.plugins.probes import Probes

class RenameVariables:
    output_folder = 'output/rename_variables'
    root = '.'

    @staticmethod
    def getName():
        return 'RenameVariables'

    rename_dict = {Sort.String: 'str', Sort.Bool: 'bool', Sort.Int: 'int', Sort.RegEx: 'rgx'}

    def __call__(self, smtfile, rename_dict=None):
        if rename_dict:
            self.rename_dict.update(rename_dict)
        # nVar = {k:len(v) for k, v in smtfile.Probes.getIntel()['variables'].items()}

        new_ast = ASTRef()
        ast = Probes().getIntel(smtfile)

        # building substitution dict (str01, str02, int01...)
        self.subst_dict = {name: f'{self.rename_dict[sort]}{str(i+1).zfill(math.floor(math.log(len(names), 10))+1)}'
                           for sort, names in ast.get_intel()['variables'].items() for i, name in enumerate(names)}

        for ass in ast:
            new_ast.add_node(self._substitute_in_node(ass))

        print(self.subst_dict)

        with smtquery.ui.output.makeFile(self._getOutputFilePath(smtfile)) as handle:
            handle.write(str(new_ast))
        new_smtfile = smtquery.storage.smt.fs.SMTFile(smtfile.getName(), self.root+"/"+self._getOutputFilePath(smtfile))
        Probes().getIntel(new_smtfile)
        return new_smtfile


    def _substitute_in_node(self, node):
        if node.kind() == Kind.VARIABLE:
            node.vDecl = self.subst_dict[node.vDecl]
        else:
            node.vChildren = list(map(self._substitute_in_node, node.children()))
        return node

    def _getOutputFilePath(self,smtfile):
        return self.output_folder+''.join(f"/{f}" for f in smtfile.getName().split(":"))


def PullExtractor():
    return [RenameVariables]