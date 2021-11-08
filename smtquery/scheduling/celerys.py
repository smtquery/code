import celery

import smtquery.solvers
import smtquery.solvers.solver

import smtquery.storage.smt

store = None

def setupCelery ():
    app = celery.Celery ("SMTQuery",
                         backend='rpc://'
                         )
    
    @app.task (name="runFunc")
    def runFunc (data):
        print (data)
        print (smtquery.solvers.solverarr)

        solver = smtquery.solvers.solverarr[data["solver"]]
        timeout = data["timeout"]
        split = data["smtname"].split (":")
        track = smtquery.storage.smt.storage.searchForTrack (split[0]) 
        if track:
            file = track.searchFile (split[1])
            res = solver.runSolver (file,timeout,store)
            return {"result" : res.getResult ().value,
                    "time" : res.getTime (),
                    "model" : res.getModel ()
                    }
            
        return "None"
    
    return app,runFunc
    

class Queue:
    def __init__(self,broker):
        self._apps,self._func = setupCelery ()
        
       
    def runSolver (self,func,smtfile,timeout):
        serialize = {"solver" : func.getName (),
                     "smtname" : smtfile.getName (),
                     "timeout" : timeout}
        return self._func.apply_async  (args =  (serialize,))

    def interpretSolverRes (self,res):
        jss = res.get ()
        return smtquery.solvers.solver.VerificationResult ( smtquery.solvers.solver.Result(jss["result"]),
                                                            jss["time"],
                                                            jss["model"]
                                                        )
        
    def workerQueue (self,storage):
        global store
        worker = self._apps.Worker ()
        store = storage
        worker.start ()
