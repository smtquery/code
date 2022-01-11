import smtquery.qlang.parser
import smtquery.qlang.interpreter
import smtquery.qlang.predicates
import smtquery.intel
import smtquery.extract
import smtquery.apply
import smtquery.ui

def getName ():
    return "qlang"

def addArguments (parser):
    return 

def run (arguments):
    interpreter = smtquery.qlang.interpreter.Interpreter ()
    query = input (">")

    predicates  = {}
    
    predicates.update(smtquery.intel.manager.predicates ().items())
    
    for name in smtquery.config.conf.getSolvers ().keys():
        predicates[f"isSAT({name})"] = smtquery.qlang.predicates.makeSatPredicate (name)

        
    extract = smtquery.extract.extractors
    applyf = smtquery.apply.applys 
    
        
    parser = smtquery.qlang.parser.Parser (predicates,smtquery.config.conf.getStorage ().storageAttributes (),extract,applyf)
    
        
    node = parser.parse (query)


               
               

    interpreter.Run (node,print)
