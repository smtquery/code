
import smtquery.config

def getName ():
    return "allocateNew"

def addArguments (parser):
    return 

def run (arguments):
    storage = smtquery.config.getConfiguration().getStorage ()
    storage.allocate_new_files_db ()
    


