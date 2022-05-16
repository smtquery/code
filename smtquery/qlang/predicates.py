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
    if smtquery.config.conf.getStorage ().getResultForSolver(smtfile,solvername)["result"] == smtquery.solvers.solver.Result.Satisfied:
        return Trool.TT
    else:
        return Trool.FF

def isUnSat (smtfile,solvername):
    if smtquery.config.conf.getStorage ().getResultForSolver(smtfile,solvername)["result"] == smtquery.solvers.solver.Result.NotSatisfied:
        return Trool.TT
    else:
        return Trool.FF

def hasValidModel (smtfile,solvername):
    if smtquery.config.conf.getStorage ().getResultForSolver(smtfile,solvername)["verified"] == smtquery.solvers.solver.Verified.VerifiedSAT:
        return Trool.TT
    else:
        return Trool.FF

def isCorrectResult (smtfile,solvername):
    if smtquery.config.conf.getStorage ().getResultForSolver(smtfile,solvername)["verified"] in [smtquery.solvers.solver.Verified.VerifiedSAT, smtquery.solvers.solver.Verified.Majority]:
        return Trool.TT
    else:
        return Trool.FF

# returns true if both solvers agree on a result and solver1 is faster than the other
def isFaster (smtfile,solver1,solver2):
    res = smtquery.config.conf.getStorage ().getResultsForInstance(smtfile)

    # compare results
    validResults = set({smtquery.solvers.solver.Result.Satisfied,smtquery.solvers.solver.Result.NotSatisfied})
    if (res[solver1]["result"] == res[solver2]["result"] and res[solver1]["time"] <= res[solver2]["time"]) or (res[solver1]["result"] in validResults and res[solver2]["result"] not in validResults):
        return Trool.TT
    else:
        return Trool.FF

def makeSatPredicate (solvername):
    def predicate (smtfile):
        return isSat (smtfile,solvername)
    return predicate

def makeUnSatPredicate (solvername):
    def predicate (smtfile):
        return isUnSat (smtfile,solvername)
    return predicate

def makeValidModelPredicate (solvername):
    def predicate (smtfile):
        return hasValidModel (smtfile,solvername)
    return predicate

def makeIsCorrectPredicate (solvername):
    def predicate (smtfile):
        return isCorrectResult (smtfile,solvername)
    return predicate

def makeFasterPredicate (solver1,solver2):
    def predicate (smtfile):
        return isFaster (smtfile,solver1,solver2)
    return predicate
