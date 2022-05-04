import smtquery.config
import smtquery.solvers.solver

import re

from smtquery.qlang.trool import *

def hasWordRegex (smtfile):
    if smtfile.OldProbes['regex'] > 0:
        return Trool.TT
    else:
        return Trool.FF

def isSat (smtfile,solvername):
    solver = smtquery.config.conf.getSolvers ()[solvername]
    schedule = smtquery.config.conf.getScheduler ()
    run_parameters = smtquery.config.conf.getRunParameters ()
    storage = smtquery.config.conf.getStorage ()
    
    # try using the database
    b_input = smtfile.getName().split(":")
    b_smtfile = storage.searchFile(b_input[0],b_input[1],b_input[2])
    if b_smtfile != None:
        b_id = b_smtfile.getId() 
        res = storage.getResultsForBenchmarkId(b_id)
        if solvername in res:
            if res[solvername]["result"] == smtquery.solvers.solver.Result.Satisfied:
                return Trool.TT
            else:
                return Trool.FF 

    # fall back
    res = schedule.runSolver (solver,smtfile,run_parameters["timeout"])
    res.wait ()
    res = schedule.interpretSolverRes (res)

    if res.getResult () == smtquery.solvers.solver.Result.Satisfied:
        return Trool.TT
    else:
        return Trool.FF

# returns true if both solvers agree on a result and solver1 is faster than the other
def isFaster (smtfile,solver1,solver2):
    solvers = [smtquery.config.conf.getSolvers ()[solver1],smtquery.config.conf.getSolvers ()[solver2]]
    schedule = smtquery.config.conf.getScheduler ()
    run_parameters = smtquery.config.conf.getRunParameters ()
    storage = smtquery.config.conf.getStorage ()
    
    b_input = smtfile.getName().split(":")
    b_smtfile = storage.searchFile(b_input[0],b_input[1],b_input[2])
    results = []
    times = []

    for s in solvers:
        c_result = None
        c_time = None
        # try using the database
        if b_smtfile != None:
            b_id = b_smtfile.getId() 
            res = storage.getResultsForBenchmarkId(b_id)
            if s.getName()  in res:
                c_result = res[s.getName()]["result"]
                c_time = res[s.getName()]["time"]
        # fall back          
        if c_result == None and c_time == None:
            print("X")
            res = schedule.runSolver (s,smtfile,run_parameters["timeout"])
            res.wait ()
            res = schedule.interpretSolverRes (res)
            storage.storeResult (res,smtfile,s)
            c_result = res.getResult ()
            c_time = res.getTime ()
        results+=[c_result]
        times+=[c_time]

    # compare results
    validResults = set({smtquery.solvers.solver.Result.Satisfied,smtquery.solvers.solver.Result.NotSatisfied})
    if (results[0] == results[1] and times[0] <= times[1]) or (results[0] in validResults and results[1] not in validResults):
        return Trool.TT
    else:
        return Trool.FF

def makeSatPredicate (solvername):
    def predicate (smtfile):
        return isSat (smtfile,solvername)
    return predicate

def makeFasterPredicate (solver1,solver2):
    def predicate (smtfile):
        return isFaster (smtfile,solver1,solver2)
    return predicate
