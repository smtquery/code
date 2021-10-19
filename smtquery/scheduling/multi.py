import multiprocessing.pool

class Queue:
    def __init__(self,N = 5):
        self._pool = multiprocessing.pool.Pool (N)

    def run (self,func,params):
        return self._pool.apply_async (func,params)

    def workerQueue (self):
        pass

