import smtquery.config

def getName ():
    return "smtworker"

def addArguments ( parser):
    return 

def run (args):
    schedule = smtquery.config.getConfiguration().getScheduler () 
    schedule.workerQueue (smtquery.config.getConfiguration().getStorage ())
    
