import enum
import subprocess
import time
import tempfile
import shutil
import os
import logging
import hashlib

class Timer:
    def __enter__ (self):
        self._l1 = time.perf_counter()
        
    def __exit__ (self,exc_type, exc_value, traceback):
        self._l2 = time.perf_counter ()

    def getElapsed (self):
        return self._l2 - self._l1
    

class Result(enum.Enum):
    Satisfied = 0
    NotSatisfied  = 1
    Unknown = 2
    TimeOut = 3
    ErrorTermination = 4

class VerificationResult:
    def __init__ (self,result: Result,
                  time_in_seconds: float,
                  model: str
                  ):
        self._result = result
        self._time_in_seconds = time_in_seconds
        self._model = model

    def getResult (self):
        return self._result

    def getTime (self):
        return self._time_in_seconds

    def getModel (self):
        return self._model

    def __str__ (self):
        return f"{self._result.name} in {self._time_in_seconds} seconds" 
    
class Solver:
    def __init__(self,command):
        self._command = command

    def getVersion (self) -> str:
        return "0.0"

    def getName (self) -> str:
        return "Dummy"

    def calcHash (self):
        with open(self._command,'br') as ff:
            return hashlib.sha256 (ff.read()).hexdigest ()
    
    def preprocessSMTFile  (self, origsmt, newsmt):
        shutil.copy(origsmt,newsmt)
    
    def postprocess (self,directory, stdout,time):
        if "unsat" in stdout:
            return VerificationResult (Result.NotSatisfied,time,"")
        elif "sat" in stdout:
            return VerificationResult (Result.Satisfied,time,"\n".join (stdout.splitlines()[1:])) 
        else:
            return VerificationResult (Result.Unknown,time,"")
        
    def buildCMDList (self,smtfilepath):
        return ["echo", smtfilepath]
    

    def runSolver (self,smtfile,timeout = None)->VerificationResult:
        with tempfile.TemporaryDirectory () as tmpdir:
            usepath = os.path.join (tmpdir,"input.smt")
            smtpath = smtfile.copyOutSMTFile (tmpdir)
            self.preprocessSMTFile (smtpath,usepath)
            
            timer = Timer ()
            try:
                with timer:
                    stdout = subprocess.check_output ( self.buildCMDList (usepath),timeout = timeout)
            except subprocess.CalledProcessError as cer:
                #Sub-process returned non-zero value
                print (cer.stdout)
                logging.getLogger ().error (f"Solver {self.getName() } returned non-zero exit code for {smtpath}")
                return VerificationResult (Result.ErrorTermination,timer.getElapsed(),"")
            except subprocess.TimeoutExpired:
                return VerificationResult (Result.TimeOut,timer.getElapsed(),"")
            return self.postprocess (tmpdir,stdout.decode(),timer.getElapsed ())
        
    def __call__ (self,params):
        return self.runSolver (*params)
    
