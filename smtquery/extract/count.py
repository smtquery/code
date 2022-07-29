import smtquery.ui
from smtquery.solvers.solver import *

class CountInstances:    
    @staticmethod
    def getName ():
        return "Count"

    def finalise(self,results,total):
        totalCount = sum([r for r in results if r != None])
        with smtquery.ui.output.makePlainMessager () as mess:
            mess.message (f"Total matching instances: {totalCount} of {total} within the selected set ({(100/total)*totalCount}%). ")
        
    def __call__  (self,smtfile):
        return 1

def PullExtractor():
    return [CountInstances]
