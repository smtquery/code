import logging
import shutil
import smtquery.solvers.cvc5
import smtquery.solvers.z3
import smtquery.solvers.solver
import yaml

solverarr = {}

def createSolver (name,binarypath):
    if name == "CVC5":
        return smtquery.solvers.cvc5.CVC5 (binarypath)
    elif name == "Z3Str3":
        return smtquery.solvers.z3.Z3 (binarypath,"Str3","z3str3")
    elif name == "Z3Seq":
        return smtquery.solvers.z3.Z3 (binarypath,"Seq","seq")
    else:
        raise "Unknown Solver Instance"


    
