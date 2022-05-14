
class Visitor:
    def visitSelect (self,node):
        pass

    def visitExtract (self,node):
        pass

    def visitExtractFunc (self,node):
        pass

    def visitExtractNode (self,node):
        pass
    
    
    def visitAllInstances (self,node):
        pass

    def visiPredicate (self,node):
        pass

    def visitTT (self,node):
        pass

    def visitFF (self,node):
        pass
    
    def visitAnd (self,node):
        pass

    def visitOr (self,node):
        pass

    def visitNot (self,node):
        pass

    def visitInstanceList (self,node):
        pass
    
    def visitBenchTrackInstances (self,node):
        pass

    def visitBenchInstances (self,node):
        pass
    
    
class QNode:
    def __init__(self,children = []):
        self._children = children
        
    def visit (self,visitor):
        visit.visitQNode (visitor)

    def __str__(self):
        return ",".join(map (str,self._children))

    def children (self):
        yield from self._children

class SelectNode (QNode):
    def __init__(self,attributes,instances,predicates):
        super().__init__ ([instances,predicates,attributes])

    def getInstance (self):
        return self._children[0]

    def getPredicate (self):
        return self._children[1]

    def getAttributes (self):
        return self._children[2]

    
    def accept (self,visit):
        visit.visitSelect (self)
    
class ExtractNode (QNode):
    def __init__(self,toextract,instances,predicates,applyf):
        super().__init__ ([toextract,instances,predicates,applyf])

    def accept (self,visit):
        visit.visitExtractNode (self)

    def getExtractFunc (self):
        return self._children[0]

    def getInstances (self):
        return self._children[1]

    def getPredicates (self):
        return self._children[2]

    def getApply (self):
        return self._children[3]
    
    
    
        
class AllInstances(QNode):
    def __init__(self):
        super().__init__ ([])

    def __str__(self):
        return "*"

    def accept (self,visit):
        visit.visitAllInstances (self)
    
class Predicate (QNode):
    def __init__ (self,name,predfunction):
        self._name = name
        self._predfunction = predfunction

    def __str__(self):
        return self._name

    def __call__(self,smtfile):
        return self._predfunction (smtfile)

    def accept (self,visit):
        visit.visitPredicate (self)

class Apply (QNode):
    def __init__ (self,name,applyfunction):
        self._name = name
        self._applyfunction = applyfunction

    def __str__(self):
        return self._name

    def __call__(self,smtfile):
        return self._applyfunction (smtfile)

    def accept (self,visit):
        visit.visitApply (self)


class ExtractFunc (QNode):
    def __init__ (self,name,extractfunction):
        self._name = name
        self._extractfunction = extractfunction

    def __str__(self):
        return self._name

    def getExtract (self):
        return self._extractfunction

    def __call__ (self,smtfile):
        return self._extractfunction (smtfile)

    def finalise(self,total):
        return self._extractfunction.finalise(total)
    
    def accept (self,visit):
        visit.visitExtractFunc (self)



        
class Attribute (QNode):
    def __init__ (self,name,attrfunction):
        self._name = name
        self._attrfunction = attrfunction

    def __str__(self):
        return self._name

    def __call__(self,smtfile):
        return self._attrfunction (smtfile)

    def accept (self,visit):
        visit.visitAttribute (self)

class AttributeList(QNode):
    def __init__(self,liste):
        super().__init__ (liste)

    def accept (self,visit):
        visit.visitAttributeList (self)


    
class TT(QNode):
    def __init__(self):
        super().__init__ ([])

    def __str__(self):
        return "True"

    def accept (self,visit):
        visit.visitTT (self)
    
    
class FF(QNode):
    def __init__(self):
        super().__init__ ([])

    def __str__(self):
        return "True"

    def accept (self,visit):
        visit.visitFF (self)
    
    
class And(QNode):
    def __init__(self,left,right):
        super().__init__ ([left,right])
        
    def accept (self,visit):
        visit.visitAnd (self)
    
   

class Or(QNode):
    def __init__(self,left,right):
        super().__init__ ([left,right])

    def accept (self,visit):
        visit.visitOr (self)


class Not(QNode):
    def __init__(self,left):
        super().__init__ ([left])

    def accept (self,visit):
        visit.visitNot (self)


class InstanceList(QNode):
    def __init__(self,liste):
        super().__init__ (liste)

    def accept (self,visit):
        visit.visitInstanceList (self)
    
class BenchTrackInstances(QNode):
    def __init__(self,benchmark, track):
        super().__init__ ([])
        self._benchmark = benchmark
        self._track = track
    
    def getBenchmark (self):
        return self._benchmark

    def getTrack (self):
        return self._track

    def __str__(self):
        return f"{self._benchmark}:{self._track}"

    def accept (self,visit):
        visit.visitBenchTrackInstances (self)

        
class BenchInstances(QNode):
    def __init__(self,benchmark):
        super().__init__ ([])
        self._benchmark = benchmark

    def getBenchmark (self):
        return self._benchmark
    
    def __str__(self):
        return f"{self._benchmark}:*"

    def accept (self,visit):
        visit.visitBenchInstances (self)

