import functools
import smtquery.storage.smt

def callback (solver,smtfile,res):
    store = smtquery.config.getConfiguration().getStorage ()
    store.storeResult (res,smtfile,solver)

def applySelect(conf,attriextractor,instance,pushres):
    return attriextractor.Extract (instance,pushres)

def applySelectCheckPred(conf,pred,attriextractor,instance,pushres):
    if pred.Check (instance) == smtquery.qlang.predicates.Trool.TT:
        return applySelect(conf,attriextractor,instance,pushres)
    
def applyExtract(node,instance):
    return node.getExtractFunc () (node.getApply  () (instance))

def applyExtractCheckPred(pred,node,instance):
    if pred.Check (instance) == smtquery.qlang.predicates.Trool.TT:
        return applyExtract(node,instance)


def callbackSelect (res):
    return res 

class Queue:
    def __init__(self):
        pass

    def runSolver (self,func,smtfiles,timeouts):
        results = []
        for smtfile,timeout in zip(smtfiles,timeouts):  
            results.append(func.runSolver(smtfile,timeout))
        return results
        #store = smtquery.config.getConfiguration().getStorage ()
        #store.storeResult (res,smtfile,func)

    def runSolverOnText (self,func,text,timeout):
        return func.runSolverOnText(text,timeout)

    def runVerification (self,si,smtfile):
        si.getResultsForInstance(smtfile)

    def interpretSolverRes (self,res):
        print (res)
        return res
    
    def runSelect (self,conf,pred,attriextractor,instance,pushres):
        return applySelectCheckPred(conf,pred,attriextractor,instance,pushres)#,callback = callbackSelect)

    def runSelectNoPred (self,conf,attriextractor,instance,pushres):
        return applySelect(conf,attriextractor,instance,pushres)#,callback = callbackSelect)
    
    def runExtract (self,pred,node,instance):
        return applyExtractCheckPred(pred,node,instance)

    def runExtractNoPred (self,node,instance):
        return applyExtract(node,instance)
    
    def workerQueue (self):
        pass

    def close (self):
        pass
