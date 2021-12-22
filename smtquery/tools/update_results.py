import smtquery.storage.smt.fs
import smtquery.scheduling


def getName ():
    return "updateResults"

def addArguments (parser):
    return 

def run (args):
    solvers = smtquery.config.conf.getSolvers ()
    storage = smtquery.config.conf.getStorage ()
    schedule = smtquery.config.conf.getScheduler ()
    ll = []
    with smtquery.ui.Progress () as progress:
        for file in storage.allFiles ():
            for key,solver in solvers.items ():
                progress.message (f"Running {key} on {file.getName ()}")
                res = schedule.runSolver (solver,file,None)#solver.runSolver (file)
                ll.append (res)
    for r in ll:
        r.wait ()
                
