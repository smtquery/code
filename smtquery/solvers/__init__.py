import logging
import shutil
import smtquery.solvers.cvc5
import smtquery.solvers.z3
import smtquery.solvers.solver
import smtquery.solvers.cvc4
import smtquery.solvers.ostrich
import yaml

solverarr = {}

def createSolver (name,binarypath):
    if name == "CVC5":
        return smtquery.solvers.cvc5.CVC5 (binarypath)
    elif name == "Z3Str3":
        return smtquery.solvers.z3.Z3 (binarypath,"Str3","z3str3")
    elif name == "Z3Seq":
        return smtquery.solvers.z3.Z3 (binarypath,"Seq","seq")
    elif name == "CVC4":
        return smtquery.solvers.cvc4.CVC4 (binarypath)
    elif name == "Ostrich":
        return smtquery.solvers.ostrich.Ostrich (binarypath)
    elif name == "Z3Noodler":
        return smtquery.solvers.z3.Z3 (binarypath,"Noodler","noodler")
    else:
        raise "Unknown Solver Instance"


    
