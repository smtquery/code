import smtquery.config
import smtquery.solvers.solver

import re

from smtquery.qlang.trool import *

def hasWordRegex (smtfile):
    if smtfile.OldProbes['regex'] > 0:
        return Trool.TT
    else:
        return Trool.FF

    
#isSat currently calls the specific solver (in future we should query the db instead)
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


def makeSatPredicate (solvername):
    def predicate (smtfile):
        return isSat (smtfile,solvername)
    return predicate
