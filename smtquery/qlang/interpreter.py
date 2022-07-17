import smtquery.config
import smtquery.qlang.predicates


class InstanceEnumerator:
    def __init__ (self):
        self._subgens = []

    def append (self,gen):
        self._subgens.append (gen)
        
    def enumerate (self):
        for gen in self._subgens:
            yield from gen


class InstanceSelector:
    def Select (self,node):
        #print (node)
        node.accept (self)
        return self._res
        
    def visitInstanceList (self,node):
        instances = InstanceEnumerator ()
        for c in node.children ():
            c.accept (self)
            instances.append (self._res)
        self._res = instances
            
    def visitBenchTrackInstances (self,node):
        storage = smtquery.config.conf.getStorage ()
        for bb in storage.getBenchmarks ():
            if node.getBenchmark ().replace(":","") == bb.getName ():
                for track in bb.tracksInBenchmark ():
                    if track.getName () == f"{node.getBenchmark()}:{node.getTrack()}":
                        self._res = track.filesInTrack ()
                
        
    def visitBenchInstances (self,node):
        storage = smtquery.config.conf.getStorage ()
        for bb in storage.getBenchmarks ():
            if node.getBenchmark () == bb.getName ():
                self._res = bb.filesInBenchmark ()
    
    def visitAllInstances (self,node):
        storage = smtquery.config.conf.getStorage ()
        self._res = storage.allFiles ()
        
class CheckPredicate:
    def __init__(self,prednode):
        self._prednode = prednode

    def Check (self,smtfile):
        self._smtfile = smtfile
        self._prednode.accept (self)
        return self._res

    def visiPredicate (self,node):
        self._res = node (self._smtfile)

    def visitTT (self,node):
        self._res = smtquery.qlang.predicates.Trool.TT
        
    def visitFF (self,node):
        self._res = smtquery.qlang.predicates.Trool.FF


    def visitPredicate (self,node):
        self._res = node(self._smtfile)
    
    def visitAnd (self,node):
        for n in node.children ():
            n.accept (self)
            if self._res != smtquery.qlang.predicates.Trool.TT:
                self._res = smtquery.qlang.predicates.Trool.FF
                return 
        self._res = smtquery.qlang.predicates.Trool.TT
    

    def visitOr (self,node):
        for n in node.children ():
            n.accept (self)
            if self._res == smtquery.qlang.predicates.Trool.TT:
                self._res = smtquery.qlang.predicates.Trool.TT
                return 
            self._res = smtquery.qlang.predicates.Trool.FF
    

    def visitNot (self,node):
        for n in node.children ():
            n.accept (self)
            if self._res == smtquery.qlang.predicates.Trool.TT:
                self._res = smtquery.qlang.predicates.Trool.FF
            elif self._res == smtquery.qlang.predicates.Trool.FF:
                self._res = smtquery.qlang.predicates.Trool.TT
            else:
                self._res = smtquery.qlang.predicates.Trool.Maybe



class Attribute:
    def __init__ (self,attri):
        self._attri = attri
        self._file = None
        
    def Extract (self,smtfile,pushres):
        self._res = []
        self._file = smtfile
        self._attri.accept(self)
        pushres (self._res)
        self._res = []
        #return self._res

    def visitAttributeList (self,node):
        for i in node.children ():
            i.accept(self)

    def visitAttribute (self,node):
        self._res.append (node (self._file))
        
    

class Interpreter:
    def Run (self,node, pushres):
        self._res = []
        self._push = pushres
        node.accept (self)
        
    def visitSelect (self,node):
        instances = InstanceSelector().Select (node.getInstance ())
        attriextractor = Attribute (node.getAttributes ())

        schedule = smtquery.config.conf.getScheduler ()
        ll = []
        with smtquery.ui.output.makeProgressor () as progress:
            plain_pred = node.getPredicate ()
            if plain_pred != None:
                pred = CheckPredicate (plain_pred)
                for i in instances.enumerate ():
                    progress.message (f"Submitting {i.getName()}")
                    res = schedule.runSelect(pred,attriextractor,i,self._push)
                    ll.append (res)
            else:
                for i in instances.enumerate ():
                    progress.message (f"Submitting {i.getName()}")
                    res = schedule.runSelectNoPred(attriextractor,i,self._push)
                    ll.append (res) 
            progress.message (f"Waiting for results ...\n")
            for r in ll:
                r.wait ()

    def visitExtractNode (self,node):
        instances = InstanceSelector().Select (node.getInstances ())
        total_checked_instances = 0

        """
        schedule = smtquery.config.conf.getScheduler ()
        ll = []
        with smtquery.ui.output.makeProgressor () as progress:
            plain_pred = node.getPredicates ()
            if plain_pred != None:
                pred = CheckPredicate (plain_pred)
                for i in instances.enumerate ():
                    progress.message (f"Submitting {i.getName()}")
                    total_checked_instances+=1
                    res = schedule.runExtract(pred,node,i)
                    ll.append (res)
            else:
                for i in instances.enumerate ():
                    progress.message (f"Submitting {i.getName()}")
                    total_checked_instances+=1
                    res = schedule.runExtractNoPred(node,i)
                    ll.append (res) 
            progress.message (f"Waiting for results ...\n")
            for r in ll:
                r.wait ()
            node.getExtractFunc ().finalise(total_checked_instances)
        """




        ###
        
        plain_pred = node.getPredicates ()
        total_checked_instances = 0
        if plain_pred != None:
            pred = CheckPredicate (plain_pred)
            for i in instances.enumerate ():
                total_checked_instances+=1
                if pred.Check (i) == smtquery.qlang.predicates.Trool.TT:
                    node.getExtractFunc () (node.getApply  () (i))
            node.getExtractFunc ().finalise(total_checked_instances)
        else:
            for i in instances.enumerate ():
                total_checked_instances+=1
                node.getExtractFunc () (node.getApply  () (i))
            node.getExtractFunc ().finalise(total_checked_instances)
    
    

    
