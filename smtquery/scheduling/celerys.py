import celery



def setupCelery ():
    app = celery.Celery ("SMTQuery",
                         backend='rpc://'
                         )
    app.conf.update (
        accept_content = ['pickle'],
        result_serializer = 'pickle'
    )
    
    @app.task (name="runFunc")
    def runFunc (func,params):
        return func(params)
    
    
    return app,runFunc
    

class Queue:
    def __init__(self,broker):
        self._apps,self._func = setupCelery ()
        
       
    def run (self,func,params):
         return self._func.apply_async  (args =  (func,params), serializer = "pickle")


    def workerQueue (self):
        worker = self._apps.Worker ()
        worker.start ()
