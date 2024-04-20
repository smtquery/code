import smtquery.solvers.solver as solver
import subprocess
import re


class Ostrich(solver.Solver):
    def __init__(self, binarypath):
        super().__init__(binarypath)
        self._path = binarypath

    def getVersion(self):
        return subprocess.check_output([self._path, "--version"])

    def getName(self):
        return "Ostrich"

    def preprocessSMTFile(self, origsmt, newsmt):
        with open(origsmt, 'r') as orig, open(newsmt, 'w') as new:
            for l in orig:
                if "(get-model" not in l:
                    new.write(l)

    def buildCMDList(self, smtfilepath):
        return [self._path, "-logo", "-version", "+quiet", "+model", smtfilepath]
