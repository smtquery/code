import smtquery.qlang.parser
import smtquery.qlang.interpreter
import smtquery.qlang.predicates

def getName ():
    return "qlang"

def addArguments (parser):
    return 

def run (arguments):
    interpreter = smtquery.qlang.interpreter.Interpreter ()
    query = input (">")

    predicates  = {}

    for i,v in smtquery.config.conf.getStorage ().storagePredicates ().items():
        predicates[i] = v

    for name in smtquery.config.conf.getSolvers ().keys():
        predicates[f"isSAT({name})"] = smtquery.qlang.predicates.makeSatPredicate (name)
        
    parser = smtquery.qlang.parser.Parser (predicates,smtquery.config.conf.getStorage ().storageAttributes ())

        
    node = parser.parse (query)


    interpreter.Run (node,print)
