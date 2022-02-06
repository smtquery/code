import smtquery.storage.smt.fs
import smtquery.scheduling


def getName ():
    return "smtsolver"

def addArguments (parser):
    parser.add_argument ('solver',type=str,default="CVC4")
    parser.add_argument ('benchmark',type=str,default="dummbench")
    parser.add_argument ('track',type=str,default="track")
    parser.add_argument ('smtfile',type=str,default="model")


def run (args):
    solver = smtquery.config.conf.getSolvers ()[args.solver]
    storage = smtquery.config.conf.getStorage ()
    schedule = smtquery.config.conf.getScheduler ()
    run_parameters = smtquery.config.conf.getRunParameters ()

    file = storage.searchFile (args.benchmark,args.track,args.smtfile)

    if file:
        res = schedule.runSolver (solver,file,run_parameters["timeout"])#solver.runSolver (file)
        res.wait ()
        print (schedule.interpretSolverRes (res))
    
