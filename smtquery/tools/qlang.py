import smtquery.qlang.parser
import smtquery.qlang.interpreter
import smtquery.qlang.predicates
import smtquery.intel
import smtquery.extract
import smtquery.apply
import smtquery.ui

from itertools import product

def getName ():
    return "qlang"

def addArguments (parser):
    return 

def run (arguments):
    interpreter = smtquery.qlang.interpreter.Interpreter ()
    query = input (">")

    predicates = {}
    predicates.update (smtquery.intel.intels.predicates ())

    for name in smtquery.config.getConfiguration().getSolvers ().keys():
        predicates[f"isSAT({name})"] = smtquery.qlang.predicates.makeSatPredicate (name)

    for name in smtquery.config.getConfiguration().getSolvers ().keys():
        predicates[f"isUNSAT({name})"] = smtquery.qlang.predicates.makeUnSatPredicate (name)

    for name in smtquery.config.getConfiguration().getSolvers ().keys():
        predicates[f"hasValidModel({name})"] = smtquery.qlang.predicates.makeValidModelPredicate (name)

    for name in smtquery.config.getConfiguration().getSolvers ().keys():
        predicates[f"isCorrect({name})"] = smtquery.qlang.predicates.makeIsCorrectPredicate (name)
    
    for s1,s2 in product(smtquery.config.getConfiguration().getSolvers ().keys(),smtquery.config.getConfiguration().getSolvers ().keys()):
        predicates[f"isFaster({s1},{s2})"] = smtquery.qlang.predicates.makeFasterPredicate (s1,s2)
        
    extract = smtquery.extract.extractors
    applyf = smtquery.apply.applys 
    
        
    parser = smtquery.qlang.parser.Parser (predicates,smtquery.config.getConfiguration().getStorage ().storageAttributes (),extract,applyf)
    
        
    node = parser.parse (query)
               

    interpreter.Run (node,print)
