import smtquery.ui
from smtquery.solvers.solver import *
from tabulate import *

class ResultsTable:
    output_folder = "./output/cactus/"

    @staticmethod
    def getName ():
        return "ResultsTable"

    def finalise(self,u_res,total):
        results = dict()
        for res in u_res:
            if res == None:
                continue

            for s in res.keys():
                if s not in results:
                    results[s] = {"SAT" : 0, "UNSAT" : 0, "Unknown" : 0, "Timeout" : 0, "Crash" : 0, "Time w/o Timeout" : 0, "Total Time" : 0}
                results[s]["Total Time"]+=res[s]["time"]
                if res[s]["result"] in [Result.NotSatisfied,Result.Satisfied,Result.Unknown]:
                    results[s]["Time w/o Timeout"]+=res[s]["time"]
                if res[s]["result"] == Result.Satisfied:
                    results[s]["SAT"]+=1
                elif res[s]["result"] == Result.NotSatisfied:
                    results[s]["UNSAT"]+=1
                elif res[s]["result"] == Result.Unknown:
                    results[s]["Unknown"]+=1
                elif res[s]["result"] == Result.TimeOut:
                    results[s]["Timeout"]+=1
                else:
                    results[s]["Crash"]+=1

        if len(list(results.keys())) > 0:
            rows = [[k] for k in results[list(results.keys())[0]].keys()]
            headers = [""]+[s for s in results.keys()]
            for s in results.keys():
                for i,e in enumerate(results[s].keys()):
                    rows[i]+=[results[s][e]]
            print(tabulate(rows, headers=headers))

    def __call__  (self,smtfile):
        # collect results
        results = dict()
        _storage = smtquery.config.getConfiguration().getStorage ()
        b_input = smtfile.getName().split(":")
        b_smtfile = _storage.searchFile(b_input[0],b_input[1],b_input[2])
        if b_smtfile != None:
            b_id = b_smtfile.getId() 
            return _storage.getResultsForInstance(smtfile)

        #with smtquery.ui.output.makePlainMessager () as mess:
        #    mess.message (smtfile.getName())

def PullExtractor():
    return [ResultsTable]
