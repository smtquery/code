import smtquery.config
import smtquery.solvers.solver
import re
from smtquery.qlang.trool import *

class SolverInteraction:
    def __init__(self):
        self._solvers = smtquery.config.getConfiguration().getSolvers ()
        self._schedule = smtquery.config.getConfiguration().getScheduler ()
        self._run_parameters = smtquery.config.getConfiguration().getRunParameters ()
        self._storage = smtquery.config.getConfiguration().getStorage ()
        self._verifiers = smtquery.config.getConfiguration().getVerifiers ()
        self._file_root = smtquery.config.getConfiguration().getSMTFilePath ()

    def getResultForSolver (self,smtfile,solvername):
        return self.getResultsForInstance(smtfile)[solvername]

    def _fetchFallBack (self,smtfile):
        results = dict()
        for key,solver in self._solvers.items ():
            results[key] = self._schedule.runSolver (solver,[smtfile],[self._run_parameters["timeout"]])
             
        f_results = dict()
        for solver,res in results.items():
            r = res.get()[0]
            f_results[solver] =  {"r_id" : None, "result" : r.getResult(), "time" : r.getTime(), "model" : r.getModel(), "verified": None}
        return f_results
    
    
    def _fetchResultsForInstance(self,smtfile):
        # try using the database
        b_input = smtfile.getName().split(":")
        b_smtfile = self._storage.searchFile(b_input[0],b_input[1],b_input[2])
        if b_smtfile == None:
            return dict()
        
        b_id = b_smtfile.getId() 
        res = self._storage._fetchResultsForBenchmarkIdFromDB(b_id)
        # make sure results are available for all solvers
        if set(res.keys()) == set(self._solvers.keys()):
            return res
        else:
            return self._fetchFallBack (b_smtfile)

    def getResultsForInstance(self,smtfile):
        results = self._fetchResultsForInstance(smtfile)
        # check if all results are verified
        if any(True if x["verified"] == None else False for x in results.values()):
            results = self._verifyResults(smtfile,results)

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
                    #self._storage.storeVerified (r,smtquery.solvers.solver.Verified.VerifiedSAT)
                    r["verified"] = smtquery.solvers.solver.Verified.VerifiedSAT
                else: 
                    #self._storage.storeVerified (r,smtquery.solvers.solver.Verified.InvalidModel)
                    r["verified"] = smtquery.solvers.solver.Verified.InvalidModel
            elif r["result"] == smtquery.solvers.solver.Result.NotSatisfied:
                r_values[False]+=1
                if verified_once:
                    already_set.add(s)
                    #self._storage.storeVerified (r,smtquery.solvers.solver.Verified.SoundnessIssue)
                    r["verified"] = smtquery.solvers.solver.Verified.SoundnessIssue
        if verified_once:
            for s in set(results.keys()).difference(already_set):
                if results[s]["result"] == smtquery.solvers.solver.Result.NotSatisfied:
                    results[s]["verified"] = smtquery.solvers.solver.Verified.SoundnessIssue
                    #self._storage.storeVerified (results[s],smtquery.solvers.solver.Verified.SoundnessIssue)
                else: 
                    #self._storage.storeVerified (results[s],smtquery.solvers.solver.Verified.Unverified)
                    results[s]["verified"] = smtquery.solvers.solver.Verified.Unverified
        
        # majority vote
        majority = None
        if not verified_once:
            if r_values[True] > r_values[False]:
                majority = smtquery.solvers.solver.Result.Satisfied
            elif r_values[True] < r_values[False]:
                majority = smtquery.solvers.solver.Result.NotSatisfied
            for s,r in results.items():
                if r["result"] == majority:
                    #self._storage.storeVerified (r,smtquery.solvers.solver.Verified.Majority)
                    r["verified"] = smtquery.solvers.solver.Verified.Majority
                    
                else:
                    #self._storage.storeVerified (r,smtquery.solvers.solver.Verified.Unverified)
                    r["verified"] = smtquery.solvers.solver.Verified.Unverified

        # check everythings set
        for s,r in results.items():
            if r["verified"] == None:
                r["verified"] = smtquery.solvers.solver.Verified.Unverified

        return results #verified_once or majority


    def _verifyModel(self,smtfile,result):
        if result["result"] == smtquery.solvers.solver.Result.Satisfied:
            return self._isValidModel(smtfile,result["model"])
        return False

    ## verification
    def _isValidModel(self,smtfile,model):
        #model = self._extractAssignment(model)
        #smt_file_path = f'{self._file_root}' + ''.join(f"/{f}" for f in smtfile.getName().split(":"))
        #ast = smtquery.smtcon.smt2expr.Z3SMTtoSExpr().getAST(smt_file_path)
        #smt_ver_text = f"{ast._getPPSMTHeader()}\n{model}\n{ast._getPPAsserts()}\n{ast._getPPSMTFooter()}"
        ll = []
        #verifier_results = []
        for key,verifier in self._verifiers.items():
            t_res = self._schedule.runVerifier(verifier,smtfile,model,self._run_parameters["timeout"])
            ll.append (t_res)                
       
        verifier_results=[r.get() == smtquery.verifiers.verifier.Validated.Validated for r in ll if r.get() != None]

        #t_res = self._schedule.interpretSolverRes (r)
        #verifier_results+=[True if t_res.getResult() == smtquery.solvers.solver.Result.Satisfied else False]

        # a least on verfier has to validate the model
        return any(verifier_results)

    


def getResultsForInstance(smtfile):
    return SolverInteraction().getResultsForInstance(smtfile)
