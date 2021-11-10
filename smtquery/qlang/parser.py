import pyparsing as pp
 
class Parser:
    def __init__(self):
        SELECT = pp.Literal ("Select")
        FROM = pp.Literal ("From")
        WHERE = pp.Literal ("Where")
        EXTRACT = pp.Literal ("Extract")
        APPLY  = pp.Literal ("Apply")
        COUNT = pp.Literal ("Count")
        
        instancedescr = pp.delimitedList (pp.Literal("*")  | pp.Regex("[a-zA-Z]+:[a-zA-Z]+") | pp.Regex("[a-zA-Z]+:\*"))
        extract = self._makeExtractParser ()
        preds = self._makePredicateParser ()

        selectparser =  SELECT + pp.Literal ("*") + FROM + instancedescr + WHERE + preds
        extractor = EXTRACT + extract + FROM + instancedescr + WHERE +preds
        self._parser = selectparser | extractor 
        
    def _makeExtractParser (self):
        return pp.delimitedList(pp.Literal ("*") | pp.Literal ("WEQ") | pp.Literal ("LINEQ") | pp.Literal ("REGEQ") | pp.Literal ("HOFUNCTION"))

    def _makePredicateParser (self):
        atoms = pp.Literal ("hasWEQ") | pp.Literal ("hasRegex") | pp.Literal ("isSAT") | pp.Literal ("True") | pp.Literal ("False")
        preds = pp.Forward ()
        lparan = pp.Literal ("(")
        rparan = pp.Literal (")")
        
        preds << ((lparan + preds + pp.Literal ("AND") + preds + rparan) |   
                  (lparan + preds +pp.Literal ("OR") + preds + rparan) |
                  (lparan + pp.Literal("NOT") + preds +  rparan) |
                  atoms)
        return preds
        
    def parse (self,string):
        print (self._parser)
        return self._parser.parseString (string,parseAll = True)
    

if __name__ == "__main__":
    parser = Parser ()
    inp = input (">")
    print (parser.parse(inp))
