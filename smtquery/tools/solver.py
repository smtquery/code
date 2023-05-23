import smtquery.storage.smt.fs
import smtquery.scheduling

import logging


def getName ():
    return "smtsolver"

def addArguments (parser):
    parser.add_argument ('solver',type=str,default="CVC4")
    parser.add_argument ('benchmark',type=str,default="dummbench")
    parser.add_argument ('track',type=str,default="track")
    parser.add_argument ('smtfile',type=str,default="model")


def run (args):    
    solver = smtquery.config.getConfiguration().getSolvers ().get(args.solver,None)    
    if not solver:
        message = f"Unknown solver {args.solver}"
        print (message)
        return
    
    storage = smtquery.config.getConfiguration().getStorage ()
    schedule = smtquery.config.getConfiguration().getScheduler ()
    run_parameters = smtquery.config.getConfiguration().getRunParameters ()
    
    
    file = storage.searchFile (args.benchmark,args.track,args.smtfile)
    if file:
        res = schedule.runSolver (solver,[file],[run_parameters["timeout"]])
        res.wait ()
        print (res.get()[0])
    else:
        print (f"Cannot find file {args.benchmark} {args.track} {args.smtfile}")
