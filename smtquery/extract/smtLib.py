import smtquery.ui
from smtquery.smtcon.expr import *
import graphviz
import os

class SMTFileExport:
    output_folder = "output/smtfiles"
    root = "."

    @staticmethod
    def getName ():
        return "SMTLib"

    def finalise(self,total): 
        pass

    def __call__  (self,smtfile):
        with smtquery.ui.output.makeFile(self._getOutputFilePath(smtfile)) as handle:
            handle.write(str(smtfile.Probes._get()))
        return smtfile

    def _getOutputFilePath(self,smtfile):
        return self.output_folder+''.join(f"/{f}" for f in smtfile.getName().split(":"))

def PullExtractor():
    return [SMTFileExport]