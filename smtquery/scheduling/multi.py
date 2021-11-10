import functools
import multiprocessing.pool
import smtquery.storage.smt

def callback (solver,smtfile,res):
    store = smtquery.storage.smt.storage
    store.storeResult (res,smtfile,solver)
    

class Queue:
    def __init__(self,N = 5):
        self._pool = multiprocessing.pool.Pool (N)

    def runSolver (self,func,smtfile,timeout):
        resfunc = functools.partial (callback,func,smtfile)
        return self._pool.apply_async (func.runSolver,(smtfile,timeout),callback = resfunc)

    def interpretSolverRes (self,res):
        return res.get ()
    
    def workerQueue (self):
        pass

