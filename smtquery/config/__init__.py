from smtquery.config.FileLocator import * 
import yaml
import smtquery.solvers
import smtquery.storage.smt
import smtquery.intel
import smtquery.scheduling
import smtquery.scheduling.multi
import smtquery.scheduling.celerys
import pickle



class Configuration:
    def __init__(self,
                 solvers,
                 storage,
                 scheduler,
                 runParameters,
                 verifiers,
                 filepath,
                 ):
        self._solvers = solvers
        self._storage = storage
        self._scheduler = scheduler
        self._runParameters = runParameters
        self._verifiers = verifiers
        self._filepath = filepath

    def getSolvers (self):
        return self._solvers

    def getVerifiers (self):
        return self._verifiers

    def getStorage (self):
        return self._storage

    def getScheduler (self):
        return self._scheduler

    def getRunParameters (self):
        return self._runParameters

    def getSMTFilePath(self):
        return self._filepath

    def cleanup(self):
        self._scheduler.close()

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
    if data["name"] == "single":
        scheduler = smtquery.scheduling.single.Queue ()
    return scheduler
        
def createStorage (data):
    if data["name"] == "FS":
        storage = smtquery.storage.smt.fs.SMTStorage (data["root"])
    if data["name"] == "DBFS":

        intels = []
        if "intels" in data:
            intels = data["intels"]
            
        storage = smtquery.storage.smt.db.DBFSStorage (data["root"],
                                                       data["engine_string"]
        )
        smtquery.intel.makeIntelManager (intels) 
    return storage

        
        
def readConfig (conffile):
    global conf
    data = yaml.load (conffile,Loader=yaml.Loader)

    # tmp store data
    with open("./data.pickle", 'wb') as handle:
        pickle.dump(data, handle, protocol=pickle.HIGHEST_PROTOCOL)

    solverarr = createSolvers (data["solvers"])
    scheduler = createFrontScheduler (data["scheduler"])
    storage = createStorage (data["SMTStore"])
    runParameters = data["runParameters"]
    verifiers = createSolvers ({k : data["solvers"][k] for k in data["verifiers"] if k in data["solvers"].keys() })
    filepath = data["SMTStore"]["root"]
    conf = Configuration (solverarr,storage,scheduler,runParameters,verifiers,filepath)
    storage.makeSolverInterAction()

# needed to potentially recreate the Configuration in a multiprocessing environment
def _readConfigPath():
    if os.path.isfile("./data.pickle"):
        with open("./data.pickle", 'rb') as handle:
            data = pickle.load(handle)
    else:
        raise("Data not found!")

    global conf
    solverarr = createSolvers (data["solvers"])
    scheduler = createFrontScheduler ({"name" : "single"}) # use single processing inside to avoid children of children 
    storage = createStorage (data["SMTStore"])
    runParameters = data["runParameters"]
    verifiers = createSolvers ({k : data["solvers"][k] for k in data["verifiers"] if k in data["solvers"].keys() })
    filepath = data["SMTStore"]["root"]
    conf = Configuration (solverarr,storage,scheduler,runParameters,verifiers,filepath)
    storage.makeSolverInterAction()
    return conf

def getConfiguration():
    global conf
    if not hasattr(smtquery.config, 'conf'):
        conf = smtquery.config._readConfigPath()
    return conf




