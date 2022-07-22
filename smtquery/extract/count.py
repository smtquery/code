import smtquery.ui
from smtquery.solvers.solver import *

class CountInstances:

    _totalCount = 0
    
    @staticmethod
    def getName ():
        return "Count"

    def finalise(self,results,total):
        with smtquery.ui.output.makePlainMessager () as mess:
            mess.message (f"Total matching instances: {self._totalCount} of {total} within the selected set ({(100/total)*self._totalCount}%). ")
        
    def __call__  (self,smtfile):
        self._totalCount+=1

def PullExtractor():
    return [CountInstances]
