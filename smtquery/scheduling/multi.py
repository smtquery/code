"""
import functools
import multiprocessing.pool
import smtquery.storage.smt

def callback (solver,smtfile,res):
    store = smtquery.config.getConfiguration().getStorage ()
    store.storeResult (res,smtfile,solver)

def applySelect(attriextractor,instance,pushres):
    return attriextractor.Extract (instance,pushres)

def applySelectCheckPred(pred,attriextractor,instance,pushres):
    if pred.Check (instance) == smtquery.qlang.predicates.Trool.TT:
        return applySelect(attriextractor,instance,pushres)

def applyExtract(node,instance):
    node.getExtractFunc () (node.getApply  () (instance))

def applyExtractCheckPred(pred,node,instance):
    if pred.Check (instance) == smtquery.qlang.predicates.Trool.TT:
        applyExtract(node,instance)


def callbackSelect (res):
    return res 

class Queue:
    def __init__(self,N = 5):
        self._pool = multiprocessing.pool.Pool (N)

    def runSolver (self,func,smtfile,timeout):
        resfunc = functools.partial (callback,func,smtfile)
        return self._pool.apply_async (func.runSolver,(smtfile,timeout),callback = resfunc)

    def runSolverOnText (self,func,text,timeout):
        resfunc = functools.partial (callback,func,text)
        return self._pool.apply_async (func.runSolverOnText,(text,timeout))

    def runVerification (self,si,smtfile):
        return self._pool.apply_async (si.getResultsForInstance,(smtfile))

    def interpretSolverRes (self,res):
        return res.get ()

    def runSelect (self,pred,attriextractor,instance,pushres):
        return self._pool.apply_async (applySelectCheckPred,(pred,attriextractor,instance,pushres),callback = callbackSelect)

    def runSelectNoPred (self,attriextractor,instance,pushres):
        return self._pool.apply_async (applySelect,(attriextractor,instance,pushres),callback = callbackSelect)
    
    def runExtract (self,pred,node,instance):
        return self._pool.apply_async (applyExtractCheckPred,(pred,node,instance))

    def runExtractNoPred (self,node,instance):
        return self._pool.apply_async (applyExtract,(node,instance))
    
    def workerQueue (self):
        pass  
"""


import functools
from pathos.multiprocessing import ProcessPool
import smtquery.storage.smt

def callback (solver,smtfile,res):
    store = smtquery.config.getConfiguration().getStorage ()
    store.storeResult (res,smtfile,solver)

def applySelect(attriextractor,instance,pushres):
    return attriextractor.Extract (instance,pushres)

def applySelectCheckPred(pred,attriextractor,instance,pushres):
    if pred.Check (instance) == smtquery.qlang.predicates.Trool.TT:
        return applySelect(attriextractor,instance,pushres)

def applyExtract(node,instance):
    return node.getExtractFunc () (node.getApply  () (instance))

def applyExtractCheckPred(pred,node,instance):
    if pred.Check (instance) == smtquery.qlang.predicates.Trool.TT:
        return applyExtract(node,instance)

def callbackSelect (res):
    return res 

class Queue:
    def __init__(self,N = 5):
        self._pool = ProcessPool(nodes=N)

    def runSolver (self,func,smtfiles,timeouts):
        #resfunc = functools.partial (callback,func,smtfile)
        #return self._pool.apipe (func.runSolver,smtfile,timeout,callback = resfunc)
        return self._pool.amap (func.runSolver,smtfiles,timeouts)
 
    def runSolverOnText (self,func,text,timeout):
        resfunc = functools.partial (callback,func,text)
        return self._pool.apipe (func.runSolverOnText,(text,timeout))

    def runVerification (self,si,smtfiles):
        #return self._pool.apipe (si.getResultsForInstance,smtfile)
        return self._pool.amap (si,smtfiles)

    def interpretSolverRes (self,res):
        return res.get ()

    def runSelect (self,pred,attriextractor,instance,pushres):
        return self._pool.apipe (applySelectCheckPred,pred,attriextractor,instance,pushres)#,callback = callbackSelect)

    def runSelectNoPred (self,attriextractor,instance,pushres):
        return self._pool.apipe (applySelect,attriextractor,instance,pushres)#,callback = callbackSelect)
    
    def runExtract (self,pred,node,instance):
        return self._pool.apipe (applyExtractCheckPred,pred,node,instance)

    def runExtractNoPred (self,node,instance):
        return self._pool.apipe (applyExtract,node,instance)
    
    def workerQueue (self):
        pass 

    def close(self):
        self._pool.close()
