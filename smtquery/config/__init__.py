from smtquery.config.FileLocator import * 
import yaml
import smtquery.solvers
import smtquery.storage.smt
import smtquery.intel
import smtquery.scheduling
import smtquery.scheduling.multi
import smtquery.scheduling.celerys



class Configuration:
    def __init__(self,
                 solvers,
                 storage,
                 scheduler
                 ):
        self._solvers = solvers
        self._storage = storage
        self._scheduler = scheduler

    def getSolvers (self):
        return self._solvers

    def getStorage (self):
        return self._storage

    def getScheduler (self):
        return self._scheduler

def createSolvers (solverdata):
    solverarr = {}
    
    for solvername,sdata in solverdata.items ():
        solverarr[solvername] = smtquery.solvers.createSolver ( solvername,sdata["binary"])
    return solverarr

def createFrontScheduler (data):
    if data["name"] == "multiprocessing":
        scheduler = smtquery.scheduling.multi.Queue (int(data["cores"]))        
    if data["name"] == "celery":
        scheduler = smtquery.scheduling.celerys.Queue ("HH")
    return scheduler
        
def createStorage (data):
    if data["name"] == "FS":
        storage = smtquery.storage.smt.fs.SMTStorage (data["root"])
    if data["name"] == "DBFS":

        intels = []
        if "intels" in data:
            intels = data["intels"]
        
        storage = smtquery.storage.smt.db.DBFSStorage (data["root"],
                                                       data["engine_string"],
                                                       smtquery.intel.makeIntelManager (intels) 
        )

    return storage

        
        
def readConfig (conffile):
    global conf
    data = yaml.load (conffile,Loader=yaml.Loader)
    solverarr = createSolvers (data["solvers"])
    scheduler = createFrontScheduler (data["scheduler"])
    storage = createStorage (data["SMTStore"])
    conf = Configuration (solverarr,storage,scheduler)
    
