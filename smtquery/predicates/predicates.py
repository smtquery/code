import smtquery.smtcon.exprfun
#from smtquery.intel.plugins import Probes
from functools import partial
from smtquery.smtcon.expr import Kind
from smtquery.smtcon.expr import Sort

class Predicate:
    def __init__(self,name,version,intels,probes):
        self._name = name
        self._version = version
        self._intels = intels
        self._probes = probes
    def getName (self):
        return self._name
    def getVersion (self):
        return self._version
    def __call__ (self, smtfile):
        return None


## hasKind Helper
def _kindHelper(kind,smtfile,p,intels):
    if kind in p.getIntel(smtfile,intels).get_intel()[p.getIntelKey2Class(intels[0])]:
        return smtquery.qlang.predicates.Trool.TT
    else:
        return smtquery.qlang.predicates.Trool.FF  

class HasWEQ(Predicate):
    def __init__(self,p):
        super().__init__('HasWEQ', '0.0.1',[smtquery.smtcon.exprfun.HasAtom],p)

    def __call__(self,smtfile):
        return _kindHelper(Kind.WEQ,smtfile,self._probes,self._intels)

class HasLinears(Predicate):
    def __init__(self,p):
        super().__init__('HasLinears', '0.0.1',[smtquery.smtcon.exprfun.HasAtom],p)

    def __call__(self, smtfile):
        return _kindHelper(Kind.LENGTH_CONSTRAINT,smtfile,self._probes,self._intels)

class HasRegex(Predicate):
    def __init__(self,p):
        super().__init__('hasRegex', '0.0.1',[smtquery.smtcon.exprfun.HasAtom],p)

    def __call__(self, smtfile):
        return _kindHelper(Kind.REGEX_CONSTRAINT,smtfile,self._probes,self._intels)

class HasHOL(Predicate):
    def __init__(self,p):
        super().__init__('hasHOL', '0.0.1',[smtquery.smtcon.exprfun.HasAtom],p)

    def __call__(self, smtfile):
        return _kindHelper(Kind.HOL_FUNCTION,smtfile,self._probes,self._intels)

class HasAtLeastCountVariables(Predicate):
    def __init__(self,p):
        super().__init__('hasAtLeastCountVariables', '0.0.1',[smtquery.smtcon.exprfun.VariableCount],p)

    def __call__(self, smtfile,var_count=5,var_type=Sort.String):
        vcs = self._probes.getIntel(smtfile,self._intels).get_intel()[self._probes.getIntelKey2Class(self._intels[0])]
        if Sort.String in vcs:
            if len(set(vcs[var_type])) >= var_count:
                return smtquery.qlang.predicates.Trool.TT
        return smtquery.qlang.predicates.Trool.FF
    
class IsQuadratic(Predicate):
    def __init__(self,p):
        super().__init__('isQuadratic', '0.0.1',[smtquery.smtcon.exprfun.VariableCount],p)

    def __call__(self, smtfile,max_vars=2):
        qudratic = True

        # check quadtratic without repecting the paths
        vcs = self._probes.getIntel(smtfile,self._intels).get_intel()[self._probes.getIntelKey2Class(self._intels[0])]
        if Sort.String in vcs:
            if not all([vcs[Sort.String][var] <= max_vars for var in vcs[Sort.String].keys()]):
                return smtquery.qlang.predicates.Trool.FF
        return smtquery.qlang.predicates.Trool.TT
        
        """
        for pv in [pv[Sort.String] for pv in Probes().getIntel(smtfile).get_intel()["pathVars"] if Sort.String in pv]:
            qudratic = all([pv[var] <= max_vars for var in pv.keys()]) and qudratic
        if qudratic:
            return smtquery.qlang.predicates.Trool.TT
        else:
            return smtquery.qlang.predicates.Trool.FF
        """

class IsSimpleRegex(Predicate):
    def __init__(self,p):
        super().__init__('isSimpleRegex', '0.0.1',[smtquery.smtcon.exprfun.RegexStructure,smtquery.smtcon.exprfun.HasAtom],p)

    def __call__(self, smtfile):
        try:
            if not self._probes.getIntel(smtfile,self._intels).get_intel()[self._probes.getIntelKey2Class(self._intels[0])]["complement"] and Kind.REGEX_CONSTRAINT in self._probes.getIntel(smtfile,self._intels).get_intel()[self._probes.getIntelKey2Class(self._intels[1])]:
                return smtquery.qlang.predicates.Trool.TT
            else:
                return smtquery.qlang.predicates.Trool.FF
        except:
            return smtquery.qlang.predicates.Trool.FF
        
class HasConcatenationRegex(Predicate):
    def __init__(self,p):
        super().__init__('hasConcatenationRegex', '0.0.1',[smtquery.smtcon.exprfun.RegexStructure,smtquery.smtcon.exprfun.HasAtom],p)

    def __call__(self, smtfile):
        try:
            if self._probes.getIntel(smtfile,self._intels).get_intel()[self._probes.getIntelKey2Class(self._intels[0])]["concatenation"] and Kind.REGEX_CONSTRAINT in self._probes.getIntel(smtfile,self._intels).get_intel()[self._probes.getIntelKey2Class(self._intels[1])]:
                return smtquery.qlang.predicates.Trool.TT
            else:
                return smtquery.qlang.predicates.Trool.FF
        except:
            return smtquery.qlang.predicates.Trool.FF
        
class HasRegexDepth(Predicate):
    def __init__(self,p):
        super().__init__('hasRegexDepth', '0.0.1',[smtquery.smtcon.exprfun.maxNesting],p)

    def __call__(self, smtfile,maxNested=50):
        if 0 < self._probes.getIntel(smtfile,self._intels).get_intel()[self._probes.getIntelKey2Class(self._intels[0])] <= maxNested:
            return smtquery.qlang.predicates.Trool.TT
        else:
            return smtquery.qlang.predicates.Trool.FF
            
class HasApproxStates(Predicate):
    def __init__(self,p):
        super().__init__('hasApproxStates', '0.0.1',[smtquery.smtcon.exprfun.stateApprox],p)

    def __call__(self, smtfile,maxApproxStates=500):
        if 0 < self._probes.getIntel(smtfile,self._intels).get_intel()[self._probes.getIntelKey2Class(self._intels[0])] <= maxApproxStates:
            return smtquery.qlang.predicates.Trool.TT
        else:
            return smtquery.qlang.predicates.Trool.FF
           
class HasMinDFAStates(Predicate):
    def __init__(self,p):
        super().__init__('hasMinDFAStates', '0.0.1',[smtquery.smtcon.exprfun.minDFA],p)

    def __call__(self, smtfile,maxStates=500):
        if 0 < self._probes.getIntel(smtfile,self._intels).get_intel()[self._probes.getIntelKey2Class(self._intels[0])] <= maxStates:
            return smtquery.qlang.predicates.Trool.TT
        else:
            return smtquery.qlang.predicates.Trool.FF

class HasRecDepth(Predicate):
    def __init__(self,p):
        super().__init__('hasRecDepth', '0.0.1',[smtquery.smtcon.exprfun.maxRecDepth],p)

    def __call__(self, smtfile,recDepth=10):
        if 0 < self._probes.getIntel(smtfile,self._intels).get_intel()[self._probes.getIntelKey2Class(self._intels[0])] <= recDepth:
            return smtquery.qlang.predicates.Trool.TT
        else:
            return smtquery.qlang.predicates.Trool.FF   

class HasNumITE(Predicate):
    def __init__(self,p):
        super().__init__('hasNumITE', '0.0.1',[smtquery.smtcon.exprfun.numITE],p)

    def __call__(self, smtfile,numITE=500):
        if 0 < self._probes.getIntel(smtfile,self._intels).get_intel()[self._probes.getIntelKey2Class(self._intels[0])] <= numITE:
            return smtquery.qlang.predicates.Trool.TT
        else:
            return smtquery.qlang.predicates.Trool.FF  
            
            
class HasNumSymbols(Predicate):
    def __init__(self,p):
        super().__init__('hasNumSymbols', '0.0.1',[smtquery.smtcon.exprfun.numSymbols],p)

    def __call__(self, smtfile,numSymb=500):
        if 0 < len(self._probes.getIntel(smtfile,self._intels).get_intel()[self._probes.getIntelKey2Class(self._intels[0])]) <= numSymb:
            return smtquery.qlang.predicates.Trool.TT
        else:
            return smtquery.qlang.predicates.Trool.FF

class HasWEQVars(Predicate):
    def __init__(self,p):
        super().__init__('hasWEQVars', '0.0.1',[smtquery.smtcon.exprfun.WeqVars],p)

    def __call__(self, smtfile,weqVars=50):
        if 0 < len(max(self._probes.getIntel(smtfile,self._intels).get_intel()[self._probes.getIntelKey2Class(self._intels[0])], key=len, default=set())) <= weqVars:
            return smtquery.qlang.predicates.Trool.TT
        else:
            return smtquery.qlang.predicates.Trool.FF
            
class HasWEQLenVars(Predicate):
    def __init__(self,p):
        super().__init__('hasWEQLenVars', '0.0.1',[smtquery.smtcon.exprfun.WeqLenVars],p)

    def __call__(self, smtfile,weqLenVars=50):
        if 0 < len(max(self._probes.getIntel(smtfile,self._intels).get_intel()[self._probes.getIntelKey2Class(self._intels[0])], key=len, default=set())) <= weqLenVars:
            return smtquery.qlang.predicates.Trool.TT
        else:
            return smtquery.qlang.predicates.Trool.FF
            
class HasLenVars(Predicate):
    def __init__(self,p):
        super().__init__('hasLenVars', '0.0.1',[smtquery.smtcon.exprfun.LenConVars],p)

    def __call__(self, smtfile,lenVars=50):
        if 0 < len(max(self._probes.getIntel(smtfile,self._intels).get_intel()[self._probes.getIntelKey2Class(self._intels[0])], key=len, default=set())) <= lenVars:
            return smtquery.qlang.predicates.Trool.TT
        else:
            return smtquery.qlang.predicates.Trool.FF
            
class HasScopeCoincidence(Predicate):
    def __init__(self,p):
        super().__init__('hasScopeCoincidence', '0.0.1',[smtquery.smtcon.exprfun.WEQProperties],p)

    def __call__(self, smtfile,scope=7):
    	prop = self._probes.getIntel(smtfile,self._intels).get_intel()[self._probes.getIntelKey2Class(self._intels[0])]
        if 0 < prop["scopeCoincidence"] <= scope:
            return smtquery.qlang.predicates.Trool.TT
        else:
            return smtquery.qlang.predicates.Trool.FF
        
class purelyPositive(Predicate):
    def __init__(self,p):
        super().__init__('purelyPositive', '0.0.1',[smtquery.smtcon.exprfun.isNegated],p)

    def __call__(self,smtfile):
        nodes = self._probes.getIntel(smtfile,self._intels).nodes
        
        while len(nodes) > 0:
            n = nodes.pop()
            if n.get_intel()[self._probes.getIntelKey2Class(self._intels[0])]:
                return smtquery.qlang.predicates.Trool.FF
            nodes+=n.children()
        return smtquery.qlang.predicates.Trool.TT