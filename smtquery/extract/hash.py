import smtquery.ui
from smtquery.solvers.solver import *

class InstanceHash:    
    @staticmethod
    def getName ():
        return "Hash"

    def finalise(self,results,total):
        names = [r for r in results if r != None]
        totalCount = len(names)
        with smtquery.ui.output.makePlainMessager () as mess:
            mess.message (f"Total matching instances: {totalCount} of {total} within the selected set ({(100/total)*totalCount}%).\n--------------------------------------------------\n")

            for n in names:
                mess.message (f"[{n}]\n")
        
    def __call__  (self,smtfile):
        return smtfile.hashContent()

def PullExtractor():
    return [InstanceHash]
