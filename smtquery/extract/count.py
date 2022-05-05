import smtquery.ui
from smtquery.solvers.solver import *

class CountInstances:
    @staticmethod
    def getName ():
        return "Count"

    def finalise(self,total):
        with smtquery.ui.output.makePlainMessager () as mess:
            mess.message (f"Total matching instances: {total}")
        
    def __call__  (self,smtfile):
        pass

def PullExtractor():
    return [CountInstances]
