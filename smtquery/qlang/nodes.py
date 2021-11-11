

class QNode:
    def __init__(self,children = []):
        self._children = children
        
    def visit (self,visitor):
        visit.visitQNode (visitor)

    def __str__(self):
        return ",".join(map (str,self._children))

class SelectNode (QNode):
    def __init__(self,instances,predicates):
        print (predicates)
        super().__init__ ([instances,predicates])

class ExtractNode (QNode):
    def __init__(self,toextract,instances,predicates):
        super().__init__ ([toextract,instances,predicates])

class AllInstances(QNode):
    def __init__(self):
        super().__init__ ([])

    def __str__(self):
        return "AlLInstances"

class hasWEQ(QNode):
    def __init__(self):
        super().__init__ ([])

    def __str__(self):
        return "hasWEQ"

class hasRegex(QNode):
    def __init__(self):
        super().__init__ ([])

    def __str__(self):
        return "hasRegex"

class isSat(QNode):
    def __init__(self):
        super().__init__ ([])

    def __str__(self):
        return "AlLInstances"

class TT(QNode):
    def __init__(self):
        super().__init__ ([])

    def __str__(self):
        return "True"

class FF(QNode):
    def __init__(self):
        super().__init__ ([])

    def __str__(self):
        return "True"

class And(QNode):
    def __init__(self,left,right):
        super().__init__ ([left,right])

   

class Or(QNode):
    def __init__(self,left,right):
        super().__init__ ([left,right])

  

class Not(QNode):
    def __init__(self,left):
        super().__init__ ([left,right])


class InstanceList(QNode):
    def __init__(self,liste):
        super().__init__ (liste)
    
    
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
    
        
class BenchInstances(QNode):
    def __init__(self,benchmark):
        super().__init__ ([])
        self._benchmark = benchmark

    def getBenchmark (self):
        return self._benchmark
    
    def __str__(self):
        return f"{self._benchmark}:*"
    
