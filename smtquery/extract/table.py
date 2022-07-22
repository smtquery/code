import smtquery.ui
from smtquery.solvers.solver import *
from tabulate import *

class ResultsTable:
    _results = dict()
    output_folder = "./output/cactus/"

    @staticmethod
    def getName ():
        return "ResultsTable"

    def finalise(self,total):
        if len(list(self._results.keys())) > 0:
            rows = [[k] for k in self._results[list(self._results.keys())[0]].keys()]
            headers = [""]+[s for s in self._results.keys()]
            for s in self._results.keys():
                for i,e in enumerate(self._results[s].keys()):
                    rows[i]+=[self._results[s][e]]
            print(tabulate(rows, headers=headers))

    def __call__  (self,smtfile):
        # collect results
        _storage = smtquery.config.getConfiguration().getStorage ()
        b_input = smtfile.getName().split(":")
        b_smtfile = _storage.searchFile(b_input[0],b_input[1],b_input[2])
        if b_smtfile != None:
            b_id = b_smtfile.getId() 
            res = _storage.getResultsForInstance(smtfile)
            for s in res.keys():
                if s not in self._results:
                    self._results[s] = {"SAT" : 0, "UNSAT" : 0, "Unknown" : 0, "Timeout" : 0, "Crash" : 0, "Time w/o Timeout" : 0, "Total Time" : 0}

                self._results[s]["Total Time"]+=res[s]["time"]
                if res[s]["result"] in [Result.NotSatisfied,Result.Satisfied,Result.Unknown]:
                    self._results[s]["Time w/o Timeout"]+=res[s]["time"]
                if res[s]["result"] == Result.Satisfied:
                    self._results[s]["SAT"]+=1
                elif res[s]["result"] == Result.NotSatisfied:
                    self._results[s]["UNSAT"]+=1
                elif res[s]["result"] == Result.Unknown:
                    self._results[s]["Unknown"]+=1
                elif res[s]["result"] == Result.TimeOut:
                    self._results[s]["Timeout"]+=1
                else:
                    self._results[s]["Crash"]+=1

        #with smtquery.ui.output.makePlainMessager () as mess:
        #    mess.message (smtfile.getName())

def PullExtractor():
    return [ResultsTable]
