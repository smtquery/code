import smtquery.config

def getName ():
    return "smtworker"

def addArguments ( parser):
    return 

def run (args):
    schedule = smtquery.config.conf.getScheduler () 
    schedule.workerQueue (smtquery.config.conf.getStorage ())
    
