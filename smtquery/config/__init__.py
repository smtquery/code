from smtquery.config.FileLocator import * 
import smtquery.solvers
import smtquery.storage.smt
import smtquery.scheduling
    
def readConfig (confdir):
    
    floc = FileLocator ([confdir])
    smtquery.solvers.createSolvers (floc)
    smtquery.scheduling.createFrontScheduler (floc)
    smtquery.storage.smt.createStorage (floc)
    
    return smtquery.solvers.solverarr,smtquery.scheduling.scheduler,smtquery.storage.smt.storage,
