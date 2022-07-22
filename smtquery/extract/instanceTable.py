import smtquery.ui
from smtquery.solvers.solver import *
from tabulate import *

class InstanceTable:
    _results = dict()

    @staticmethod
    def getName ():
        return "InstanceTable"

    def finalise(self,total):
        if len(list(self._results.keys())) > 0:
            headers = ["Instance"]
            for s in self._results[list(self._results.keys())[0]].keys():
                headers+=[f"Result {s}",f"Time {s}"]
            rows = []
            for i in self._results.keys():
                c_row = [i]
                for s in self._results[i].keys():
                    c_row+=list(self._results[i][s].values())
                rows+=[c_row]
            print(tabulate(rows, headers=headers))

    def __call__  (self,smtfile):
        # collect results
        _storage = smtquery.config.getConfiguration().getStorage ()
        b_input = smtfile.getName().split(":")
        b_smtfile = _storage.searchFile(b_input[0],b_input[1],b_input[2])
        if b_smtfile != None:
            if smtfile.getName() not in self._results:
                self._results[smtfile.getName()] = dict()

            b_id = b_smtfile.getId() 
            res = _storage.getResultsForInstance(smtfile)
            for s in res.keys():
                self._results[smtfile.getName()][s] = {"Result" : res[s]["result"].name, "Time" : res[s]["time"]}

def PullExtractor():
    return [InstanceTable]
