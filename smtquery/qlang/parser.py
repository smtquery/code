import functools
import pyparsing as pp
import smtquery.qlang.nodes

def createSelect (s,l,toks):
    tokd = token2Dict(toks)
    if "WHERE" not in tokd:
        tokd["WHERE"] = None
    return smtquery.qlang.nodes.SelectNode (tokd["SELECT"],tokd["FROM"],tokd["WHERE"])

def createExtract (s,l,toks):
    tokd = token2Dict(toks)
    if "WHERE" not in tokd:
        tokd["WHERE"] = None
    if "APPLY" not in tokd:
        tokd["APPLY"] = smtquery.qlang.nodes.Apply("DummyApply",smtquery.apply.dummy.DummyApply())
    return smtquery.qlang.nodes.ExtractNode (tokd["EXTRACT"],tokd["FROM"],tokd["WHERE"],tokd["APPLY"])

def makePredicate (name,pred,s,l,toks):
    return smtquery.qlang.nodes.Predicate(name,pred)

def makeExtract (name,pred,s,l,toks):
    return smtquery.qlang.nodes.ExtractFunc(name,pred)

def makeApply (name,pred,s,l,toks):
    return smtquery.qlang.nodes.Apply(name,pred)


def makeAttribute (name,attribute,s,l,toks):
    return smtquery.qlang.nodes.Attribute(name,attribute)


def token2Dict(toks):
    tokd = dict()
    i = 0
    while i < len(toks):
        tokd[toks[i].upper()] = toks[i+1]
        i+=2
    return tokd

class Parser:
    def __init__(self,predicates = {}, attributes = {},
                 extractfunc = {}, applyfunc = {}
                 ):
        SELECT = pp.CaselessLiteral ("Select")
        FROM = pp.CaselessLiteral ("From")
        WHERE = pp.CaselessLiteral ("Where")
        EXTRACT = pp.CaselessLiteral ("Extract")
        APPLY  = pp.CaselessLiteral ("Apply")
        COUNT = pp.CaselessLiteral ("Count")
        
        instancedescr = pp.delimitedList (pp.Literal("*").setParseAction (lambda s,l,t: smtquery.qlang.nodes.AllInstances())  |
                                          pp.Regex("[a-zA-Z0-9_]+:[a-zA-Z0-9_]+").setParseAction (lambda s,l,t: smtquery.qlang.nodes.BenchTrackInstances(*t[0].split(":"))) |
                                          pp.Regex("[a-zA-Z0-9_]+").setParseAction (lambda s,l,t: smtquery.qlang.nodes.BenchInstances(t[0].split(":")[0]))
                                          ).setParseAction (lambda s,l,t: smtquery.qlang.nodes.InstanceList (t))
        extract = self._makeExtractParser (extractfunc)
        applyf = self._makeApplyParser (applyfunc)
        preds = self._makePredicateParser (predicates)
        smtattr = self._makeSMTAttributeParser (attributes)
        
        selectparser =  (SELECT + smtattr + FROM + instancedescr + pp.Optional(WHERE + preds)).setParseAction (createSelect)
        extractor = EXTRACT + extract + FROM + instancedescr + pp.Optional(WHERE + preds) + pp.Optional(APPLY + applyf)
        self._parser = selectparser | extractor.setParseAction(createExtract)

    def _makeSMTAttributeParser (self,attributes):
        attri = None
        for name,mattr in attributes.items():
            lit = pp.Literal (name).setParseAction (functools.partial (makeAttribute,name,mattr))
            if attri:
                attri = attri | lit
            else:
                attri  = lit
        return pp.delimitedList(attri).setParseAction (lambda s,l,t: smtquery.qlang.nodes.AttributeList (t)) 
                                
    def _makeExtractParser (self,extracts):
        atoms = None
        for name,pred in extracts.items():
            ll = pp.Literal (name).setParseAction (functools.partial (makeExtract,name,pred) )
            if atoms == None:
                atoms = ll
            else:
                atoms = atoms | ll
        return atoms

    def _makeApplyParser (self,applyf):
        atoms = None
        for name,pred in applyf.items():
            ll = pp.Literal (name).setParseAction (functools.partial (makeApply,name,pred) )
            if atoms == None:
                atoms = ll
            else:
                atoms = atoms | ll
        return atoms
    
    
    def _makePredicateParser (self,predicates):
        atoms = pp.CaselessLiteral ("True").setParseAction (lambda s,l,t: smtquery.qlang.nodes.TT()) | pp.CaselessLiteral ("False").setParseAction (lambda s,l,t: smtquery.qlang.nodes.FF())
        
        for name,pred in predicates.items():
            atoms = atoms | pp.Literal (name).setParseAction (functools.partial (makePredicate,name,pred) )
        
        preds = pp.Forward ()
        lparan = pp.Literal ("(")
        rparan = pp.Literal (")")
        
        preds << ((lparan + preds + pp.CaselessLiteral ("AND") + preds + rparan).setParseAction (lambda s,l,t: smtquery.qlang.nodes.And (t[1],t[3]))  |   
                  (lparan + preds +pp.CaselessLiteral ("OR") + preds + rparan).setParseAction (lambda s,l,t: smtquery.qlang.nodes.Or (t[1],t[3])) |
                  (lparan + pp.CaselessLiteral("NOT") + preds +  rparan).setParseAction (lambda s,l,t: smtquery.qlang.nodes.Not (t[2])) |
                  
                  atoms.setParseAction (lambda s,l,t: t[0]))
        return preds.setParseAction (lambda s,l,t: t[0])
        
    def parse (self,string):
        return self._parser.parseString (string,parseAll = True)[0]
    
    
