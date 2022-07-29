import smtquery.storage.smt.fs
import smtquery.scheduling

def getName ():
    return "updateResults"

def addArguments (parser):
    return 

def storeResult (solver,smtfile,res):
    store = smtquery.config.getConfiguration().getStorage ()
    store.storeResult (res,smtfile,solver)

def storeVerified (r):
    store = smtquery.config.getConfiguration().getStorage ()
    store.storeVerified (r,r["verified"])

def run (args):
    solvers = smtquery.config.getConfiguration().getSolvers ()
    storage = smtquery.config.getConfiguration().getStorage ()
    schedule = smtquery.config.getConfiguration().getScheduler ()
    run_parameters = smtquery.config.getConfiguration().getRunParameters ()
    files = list(storage.allFiles ())

    results = dict()
    with smtquery.ui.output.makeProgressor () as progress:
        for key,solver in solvers.items ():
            results[key] = schedule.runSolver (solver,files,[run_parameters["timeout"]]*len(files))
            progress.message (f"Submitting {key} jobs.")

        while not all([results[k].ready() for k in solvers.keys()]):
            progress.message (f"Waiting for results ... ")
    
    # store results
    for k in results.keys():
        for file,res in zip(files,results[k].get()):
            storeResult (solvers[k],file,res)

    ## verification
    results = dict()
    with smtquery.ui.output.makeProgressor () as progress:
        results = schedule.runVerification (smtquery.utils.solverIntegration.getResultsForInstance,files)

        while not results.ready():
            progress.message (f"Waiting for verification results ... ")

    # store results
    for res in results.get():
        for s,r in res.items():
            storeVerified (r)



    """
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
    """


    """
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
    """         
