import smtquery.ui
from smtquery.solvers.solver import *
from tabulate import *

class InstanceTable:

    @staticmethod
    def getName ():
        return "InstanceTable"

    def finalise(self,results,total):
        t_results = dict()
        for d in results:
            if d != None:
                t_results.update(d)
        if len(list(t_results.keys())) > 0:
            headers = ["Instance"]
            for s in t_results[list(t_results.keys())[0]].keys():
                headers+=[f"Result {s}",f"Time {s}"]
            rows = []
            for i in t_results.keys():
                c_row = [i]
                for s in t_results[i].keys():
                    c_row+=list(t_results[i][s].values())
                rows+=[c_row]
            print(tabulate(rows, headers=headers))

    def __call__  (self,smtfile):
        # collect results
        results = dict()
        _storage = smtquery.config.getConfiguration().getStorage ()
        b_input = smtfile.getName().split(":")
        b_smtfile = _storage.searchFile(b_input[0],b_input[1],b_input[2])
        if b_smtfile != None:
            if smtfile.getName() not in results:
                results[smtfile.getName()] = dict()

            b_id = b_smtfile.getId() 
            res = _storage.getResultsForInstance(smtfile)
            for s in res.keys():
                results[smtfile.getName()][s] = {"Result" : res[s]["result"].name, "Time" : res[s]["time"]}
        return results

def PullExtractor():
    return [InstanceTable]
