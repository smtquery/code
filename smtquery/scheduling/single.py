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

class Wrapper:
    def __init__(self,r):
        self._r = r

    def get (self):
        return self._r

    def wait (self):
        pass

    def ready (self):
        return True
    
class Queue:
    def __init__(self):
        pass

    def runSolver (self,func,smtfiles,timeouts):
        results = []
        for smtfile,timeout in zip(smtfiles,timeouts):  
            results.append(func.runSolver(smtfile,timeout))
        return Wrapper (results)
        #store = smtquery.config.getConfiguration().getStorage ()
        #store.storeResult (res,smtfile,func)

    def runVerifier (self,func,smtfile,model,timeout):
        return Wrapper(func.verifyModel (smtfile,model,timeout))
    
    
    def runVerification (self,si,smtfiles):
        results = []
        for smtfile in smtfiles:  
            results.append(si(smtfile))
        return Wrapper (results)

    def runSelect (self,conf,pred,attriextractor,instance,pushres):
        return Wrapper(applySelectCheckPred(conf,pred,attriextractor,instance,pushres))#,callback = callbackSelect)

    def runSelectNoPred (self,conf,attriextractor,instance,pushres):
        return Wrapper(applySelect(conf,attriextractor,instance,pushres))#,callback = callbackSelect)
    
    def runExtract (self,pred,node,instance):
        return Wrapper(applyExtractCheckPred(pred,node,instance))

    def runExtractNoPred (self,node,instance):
        return Wrapper(applyExtract(node,instance))
    
    def workerQueue (self):
        pass

    def close (self):
        pass
