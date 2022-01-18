import smtquery.config
import smtquery.solvers.solver

import enum

class Trool(enum.Enum):
    TT = 0
    FF = 1
    Maybe = 2



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
