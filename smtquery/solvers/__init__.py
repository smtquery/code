import logging
import shutil
import smtquery.solvers.cvc4
import smtquery.solvers.z3
import yaml

def createSolver (name,binarypath):
    if name == "CVC4":
        return smtquery.solvers.cvc4.CVC4 (binarypath)
    elif name == "Z3Str3":
        return smtquery.solvers.z3.Z3 (binarypath,"Str3","z3str3")
    elif name == "Z3Seq":
        return smtquery.solvers.z3.Z3 (binarypath,"Seq","seq")
    else:
        raise "Unknown Solver Instance"

def createSolvers (filelocator):
    conffile = filelocator.findFile ("solvers.yml")
    solverarr = {}
    if conffile:
        with open (conffile,'r') as ff:
            data = yaml.load (ff)
            for solvername,sdata in data["solvers"].items ():
                solverarr[solvername] = createSolver ( solvername,sdata["binary"])
        return solverarr
    else:
        for name,binary in [("CVC4","cvc4"),("Z3Str3","z3"),("Z3Seq","z3")]:
            bin = shutil.which  (binary)
            if bin:
                solverarr[name] = createSolver (name,bin)
        return solverarr
        
    
