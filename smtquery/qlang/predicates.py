import smtquery.config
import smtquery.solvers.solver
import re
from smtquery.qlang.trool import *


class SolverInteraction:
    def __init__(self):
        self._solvers = smtquery.config.conf.getSolvers ()
        self._schedule = smtquery.config.conf.getScheduler ()
        self._run_parameters = smtquery.config.conf.getRunParameters ()
        self._storage = smtquery.config.conf.getStorage ()
        self._verifiers = smtquery.config.conf.getVerifiers ()
        self._file_root = smtquery.config.conf.getSMTFilePath ()

    def getResultForSolver (self,smtfile,solvername):
        return self.getResultsForInstance(smtfile)[solvername]

    def _fetchResultsForInstance(self,smtfile):
        # try using the database
        b_input = smtfile.getName().split(":")
        b_smtfile = self._storage.searchFile(b_input[0],b_input[1],b_input[2])
        if b_smtfile != None:
            b_id = b_smtfile.getId() 
            res = self._storage.getResultsForBenchmarkId(b_id)
            # make sure results are available for all solvers
            if set(res.keys()) == set(self._solvers.keys()):
                return res
            # fall back
            ll = []
            for key,solver in self._solvers.items ():
                res = self._schedule.runSolver (solver,smtfile,self._run_parameters["timeout"])
                ll.append (res)                
            for r in ll:
                r.wait ()
                res = self._schedule.interpretSolverRes (r)
                self._storage.storeResult (res,smtfile,solver)
            return self._storage.getResultsForBenchmarkId(b_id)
        return dict()

    def getResultsForInstance(self,smtfile):
        results = self._fetchResultsForInstance(smtfile)

        # check if all results are verified
        if any(True if x["verified"] == None else False for x in results.values()):
            v_res = self._verifyResults(smtfile,results)

        # cvc4 as verifier fails sometimes due to smtlib 2.6 ouput!
        return results

    def _verifyResults(self,smtfile,results):
        r_values = {True: 0, False: 0}
        verified_once = False
        already_set = set()

        for s,r in results.items():
            if r["result"] == smtquery.solvers.solver.Result.Satisfied:
                already_set.add(s)
                model_verified = self._verifyModel(smtfile,r)
                r_values[True]+=1
                if model_verified:
                    verified_once = True
                    self._storage.storeVerified (r,smtquery.solvers.solver.Verified.VerifiedSAT)
                else: 
                    self._storage.storeVerified (r,smtquery.solvers.solver.Verified.InvalidModel)
            elif r["result"] == smtquery.solvers.solver.Result.NotSatisfied:
                r_values[False]+=1
                if verified_once:
                    already_set.add(s)
                    self._storage.storeVerified (r,smtquery.solvers.solver.Verified.SoundnessIssue)
        if verified_once:
            for s in set(results.keys()).difference(already_set):
                if results[s]["result"] == smtquery.solvers.solver.Result.NotSatisfied:
                    self._storage.storeVerified (results[s],smtquery.solvers.solver.Verified.SoundnessIssue)
                else: 
                    self._storage.storeVerified (results[s],smtquery.solvers.solver.Verified.Unverified)
        
        # majority vote
        majority = None
        if not verified_once:
            if r_values[True] > r_values[False]:
                majority = smtquery.solvers.solver.Result.Satisfied
            elif r_values[True] < r_values[False]:
                majority = smtquery.solvers.solver.Result.NotSatisfied
            for s,r in results.items():
                if r["result"] == majority:
                    self._storage.storeVerified (r,smtquery.solvers.solver.Verified.Majority)
                else:
                    self._storage.storeVerified (r,smtquery.solvers.solver.Verified.Unverified)
        return verified_once or majority


    def _verifyModel(self,smtfile,result):
        if result["result"] == smtquery.solvers.solver.Result.Satisfied:
            return self._isValidModel(smtfile,result["model"])
        return False

    ## verification
    def _isValidModel(self,smtfile,model):
        model = self._extractAssignment(model)
        smt_file_path = f'{self._file_root}' + ''.join(f"/{f}" for f in smtfile.getName().split(":"))
        ast = smtquery.smtcon.smt2expr.Z3SMTtoSExpr().getAST(smt_file_path)
        smt_ver_text = f"{ast._getPPSMTHeader()}\n{model}\n{ast._getPPAsserts()}\n{ast._getPPSMTFooter()}"
        ll = []
        verifier_results = []
        for key,verifier in self._verifiers.items():
                t_res = self._schedule.runSolverOnText(verifier,smt_ver_text,self._run_parameters["timeout"])
                ll.append (t_res)                
        for r in ll:
            r.wait ()
            t_res = self._schedule.interpretSolverRes (r)
            verifier_results+=[True if t_res.getResult() == smtquery.solvers.solver.Result.Satisfied else False]

        # a least on verfier has to validate the model
        return any(verifier_results)

    def _extractAssignment(self,model):
        s = ""
        for l in model:
            s+=l.rstrip("\n")
        if s.startswith("(model"):
            return s[len("(model"):-1]
        elif s.startswith("sat("):
            return s[len("sat("):-1]
        else:
            return s[len("("):-1]

    ## SolverInteraction needs a better PLACE!
    

def hasWordRegex (smtfile):
    if smtfile.OldProbes['regex'] > 0:
        return Trool.TT
    else:
        return Trool.FF

def isSat (smtfile,solvername):
    si = SolverInteraction()
    if si.getResultForSolver(smtfile,solvername)["result"] == smtquery.solvers.solver.Result.Satisfied:
        return Trool.TT
    else:
        return Trool.FF

# returns true if both solvers agree on a result and solver1 is faster than the other
def isFaster (smtfile,solver1,solver2):
    si = SolverInteraction()
    res = si.getResultsForInstance(smtfile)

    # compare results
    validResults = set({smtquery.solvers.solver.Result.Satisfied,smtquery.solvers.solver.Result.NotSatisfied})
    if (res[solver1]["result"] == res[solver2]["result"] and res[solver1]["time"] <= res[solver2]["time"]) or (res[solver1]["result"] in validResults and res[solver2]["result"] not in validResults):
        return Trool.TT
    else:
        return Trool.FF

def makeSatPredicate (solvername):
    def predicate (smtfile):
        return isSat (smtfile,solvername)
    return predicate

def makeFasterPredicate (solver1,solver2):
    def predicate (smtfile):
        return isFaster (smtfile,solver1,solver2)
    return predicate
