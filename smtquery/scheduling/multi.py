import multiprocessing.pool

class Queue:
    def __init__(self,N = 5):
        self._pool = multiprocessing.pool.Pool (N)

    def runSolver (self,func,smtfile,timeout):
        return self._pool.apply_async (func.runSolver,(smtfile,timeout))

    def interpretSolverRes (self,res):
        return res.get ()
    
    def workerQueue (self):
        pass

