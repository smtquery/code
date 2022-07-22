import smtquery.storage.smt.fs
import smtquery.scheduling
from smtquery.utils.solverIntegration import *

def getName ():
    return "updateResults"

def addArguments (parser):
    return 

def run (args):
    solvers = smtquery.config.getConfiguration().getSolvers ()
    storage = smtquery.config.getConfiguration().getStorage ()
    schedule = smtquery.config.getConfiguration().getScheduler ()
    run_parameters = smtquery.config.getConfiguration().getRunParameters ()
    ll = []
    with smtquery.ui.output.makeProgressor () as progress:
        for file in storage.allFiles ():
            for key,solver in solvers.items ():
                progress.message (f"Submitting {key} to {file.getName ()}")
                res = schedule.runSolver (solver,file,run_parameters["timeout"])
                ll.append (res)
        progress.message (f"Waiting for results ... ")
                
        for r in ll:
            r.wait ()

        ll = []
        # verification (we perform the verification at this stage to have all results stored in the db)
        for file in storage.allFiles ():
            for key,solver in solvers.items ():
                progress.message (f"Submitting {key} to {file.getName ()}")
                res = schedule.runVerification (SolverInteraction(),file)
                ll.append (res)
        progress.message (f"Waiting for verification results ... ")
                
        for r in ll:
            r.wait ()
                
