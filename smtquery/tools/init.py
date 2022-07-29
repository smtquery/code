
import smtquery.config

def getName ():
    return "initdb"

def addArguments (parser):
    return 

def run (arguments):
    storage = smtquery.config.getConfiguration().getStorage ()
    storage.initialise_db ()
    


