import pyparsing as pp
import nodes


def createSelect (s,l,toks):
    return nodes.SelectNode (toks[3],toks[5])

def createExtract (s,l,toks):
    return nodes.ExtractNode (toks[1],toks[3],toks[5])
    

class Parser:
    def __init__(self):
        SELECT = pp.Literal ("Select")
        FROM = pp.Literal ("From")
        WHERE = pp.Literal ("Where")
        EXTRACT = pp.Literal ("Extract")
        APPLY  = pp.Literal ("Apply")
        COUNT = pp.Literal ("Count")
        
        instancedescr = pp.delimitedList (pp.Literal("*").setParseAction (lambda s,l,t: nodes.AllInstances())  |
                                          pp.Regex("[a-zA-Z]+:[a-zA-Z]+").setParseAction (lambda s,l,t: nodes.BenchTrackInstances(*t[0].split(":"))) |
                                          pp.Regex("[a-zA-Z]+:\*").setParseAction (lambda s,l,t: nodes.BenchInstances(t[0].split(":")[0]))
                                          ).setParseAction (lambda s,l,t: nodes.InstanceList (t))
        extract = self._makeExtractParser ()
        preds = self._makePredicateParser ()

        selectparser =  (SELECT + pp.Literal ("*") + FROM + instancedescr + WHERE + preds).setParseAction (createSelect)
        extractor = EXTRACT + extract + FROM + instancedescr + WHERE +preds
        self._parser = selectparser | extractor .setParseAction(createExtract)
        
    def _makeExtractParser (self):
        return pp.delimitedList(pp.Literal ("*") | pp.Literal ("WEQ") | pp.Literal ("LINEQ") | pp.Literal ("REGEQ") | pp.Literal ("HOFUNCTION"))

    def _makePredicateParser (self):
        atoms = (pp.Literal ("hasWEQ").setParseAction (lambda s,l,t: nodes.hasWEQ ()) |
                 pp.Literal ("hasRegex").setParseAction (lambda s,l,t: nodes.hasRegex()) |
                 pp.Literal ("isSAT").setParseAction (lambda s,l,t: nodes.isSat ()) |
                 pp.Literal ("True").setParseAction (lambda s,l,t: nodes.TT()) |
                 pp.Literal ("False").setParseAction (lambda s,l,t: nodes.FF())
                 )
        preds = pp.Forward ()
        lparan = pp.Literal ("(")
        rparan = pp.Literal (")")
        
        preds << ((lparan + preds + pp.Literal ("AND") + preds + rparan).setParseAction (lambda s,l,t: nodes.And (t[1],t[3]))  |   
                  (lparan + preds +pp.Literal ("OR") + preds + rparan).setParseAction (lambda s,l,t: nodes.Or (t[1],t[3])) |
                  (lparan + pp.Literal("NOT") + preds +  rparan).setParseAction (lambda s,l,t: nodes.Not (t[1],t[1])) |
                  
                  atoms.setParseAction (lambda s,l,t: t[0]))
        return preds.setParseAction (lambda s,l,t: t[0])
        
    def parse (self,string):
        print (self._parser)
        return self._parser.parseString (string,parseAll = True)
    

if __name__ == "__main__":
    parser = Parser ()
    inp = "Extract * From Kaluzat:*,Kaluzat:* Where (hasWEQ AND hasWEQ)"
    print (str(parser.parse(inp)[0]))
