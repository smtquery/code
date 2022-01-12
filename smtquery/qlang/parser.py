import functools
import pyparsing as pp
import smtquery.qlang.nodes


def createSelect (s,l,toks):
    return smtquery.qlang.nodes.SelectNode (toks[1],toks[3],toks[5])

def createExtract (s,l,toks):
    return smtquery.qlang.nodes.ExtractNode (toks[1],toks[3],toks[5],toks[7])

def makePredicate (name,pred,s,l,toks):
    return smtquery.qlang.nodes.Predicate(name,pred)

def makeExtract (name,pred,s,l,toks):
    return smtquery.qlang.nodes.ExtractFunc(name,pred)

def makeApply (name,pred,s,l,toks):
    return smtquery.qlang.nodes.Apply(name,pred)


def makeAttribute (name,attribute,s,l,toks):
    return smtquery.qlang.nodes.Attribute(name,attribute)




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
                                          pp.Regex("[a-zA-Z]+:[a-zA-Z]+:\*").setParseAction (lambda s,l,t: smtquery.qlang.nodes.BenchTrackInstances(*t[0].split(":")[:-1])) |
                                          pp.Regex("[a-zA-Z]+:\*").setParseAction (lambda s,l,t: smtquery.qlang.nodes.BenchInstances(t[0].split(":")[0]))
                                          ).setParseAction (lambda s,l,t: smtquery.qlang.nodes.InstanceList (t))
        extract = self._makeExtractParser (extractfunc)
        applyf = self._makeApplyParser (applyfunc)
        preds = self._makePredicateParser (predicates)
        smtattr = self._makeSMTAttributeParser (attributes)
        
        selectparser =  (SELECT + smtattr + FROM + instancedescr + WHERE + preds).setParseAction (createSelect)
        extractor = EXTRACT + extract + FROM + instancedescr + WHERE +preds + APPLY + applyf
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
    
    
