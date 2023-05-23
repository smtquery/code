import os
import shutil
import sqlalchemy
import datetime
import time
import logging
import smtquery.solvers.solver
import hashlib
import smtquery.config
import smtquery.ui
import smtquery.intel
from smtquery.utils.solverIntegration import SolverInteraction

class SMTFile:
    def __init__(self,name,filepath,id):
        assert (os.path.exists(filepath))
        self._name = name
        self._filepath = filepath
        self._id = id
        
    def __reduce__ (self):
        return SMTFile,(self._name,self._filepath,self._id)
        
    def SMTString (self):
        with open(self._filepath,'r') as ff:
            return ff.read ()
        
    
    def hashContent (self):
        with open(self._filepath,'r') as ff:
            return hashlib.sha256 (ff.read().encode ()).hexdigest ()

    def copyOutSMTFile (self,directory):
        name = os.path.split (self._filepath)[1]
        shutil.copyfile (self._filepath,os.path.join (directory,name))
        return os.path.join (directory,name)
    
    def getName (self):
        return self._name

    def getId (self):
        return self._id

    def getFilepath (self):
        return self._filepath
    
    def __str__ (self):
        return self.SMTString ()
    
class Track:
    def __init__ (self,name,engine,id,instance_table,makesmt):
        self._engine = engine
        self._id = id
        self._name = name
        self._instance_table = instance_table
        self._makesmt = makesmt

    def filesInTrack (self):
        with self._engine.connect () as conn:
            res = conn.execute (self._instance_table.select().where (self._instance_table.c.track_id == self._id))
            for row in res.fetchall ():
                yield self._makesmt (row.name,row.path,row.id)
                
    def getName (self):
        return self._name


class Benchmark:
    def __init__ (self,name,engine,id,trackstable,instancetable,makesmt):
        self._engine = engine
        self._id = id
        self._name = name
        self._tracks_table = trackstable
        self._instancetable = instancetable
        self._makesmt = makesmt
        
    def tracksInBenchmark (self):
        with self._engine.connect () as conn:
            res = conn.execute (self._tracks_table.select().where (self._tracks_table.c.bench_id == self._id))
            for row in res.fetchall ():
                yield Track (row.name,self._engine,row.id,self._instancetable,self._makesmt)
            
    def filesInBenchmark (self):
        for track in self.tracksInBenchmark():
            yield from track.filesInTrack ()
        
    def getName (self):
        return self._name

# needed for multiprocessing
def smtfile_getName(smtfile):
    return smtfile.getName()

def smtfile_hashContent(smtfile):
    return smtfile.hashContent()

def smtfile_SMTString(smtfile):
    return smtfile.SMTString()
    
class DBFSStorage:
    def __init__ (self,root,enginestring,intels = None):
        self._root = os.path.abspath(root)        
        self._engine = sqlalchemy.create_engine(enginestring)
        
        self._meta = sqlalchemy.MetaData ()
        
        self._benchmark_table  = sqlalchemy.Table ('benchmark',self._meta,
                               sqlalchemy.Column ('id',sqlalchemy.Integer,primary_key = True),
                               sqlalchemy.Column ('name',sqlalchemy.String (255),nullable = False)
                               )

        self._tracks_table = sqlalchemy.Table ('track',self._meta,
                                 sqlalchemy.Column ('id',sqlalchemy.Integer,primary_key = True),
                                 sqlalchemy.Column ('name',sqlalchemy.String (255),nullable = False),
                                 sqlalchemy.Column ('bench_id',sqlalchemy.Integer,sqlalchemy.ForeignKey('benchmark.id'),nullable=False)
                                    )

        self._instance_table = sqlalchemy.Table ('instance', self._meta,
                             sqlalchemy.Column ('id',sqlalchemy.Integer,primary_key = True),
                             sqlalchemy.Column ('path',sqlalchemy.String(1024)),
                             sqlalchemy.Column ('name',sqlalchemy.String(255)),
                             sqlalchemy.Column ('track_id',sqlalchemy.Integer,sqlalchemy.ForeignKey('track.id'),nullable=False),
                                                 )  
        

        self._result_table = sqlalchemy.Table ('verification_result', self._meta,
                                 sqlalchemy.Column ('id',sqlalchemy.Integer,primary_key = True),
                                 sqlalchemy.Column ('instance_id',sqlalchemy.Integer,sqlalchemy.ForeignKey('instance.id'),nullable=False),
                                 sqlalchemy.Column ('result',sqlalchemy.Enum(smtquery.solvers.solver.Result),nullable=False),
                                 sqlalchemy.Column ('solver', sqlalchemy.String (255),nullable=False),
                                 sqlalchemy.Column ('time', sqlalchemy.Float,nullable=False),
                                 sqlalchemy.Column ('model', sqlalchemy.Text),
                                 sqlalchemy.Column ('date', sqlalchemy.DateTime),
                                 )

        self._validated_table = sqlalchemy.Table ('valdidated_results', self._meta,
                                 sqlalchemy.Column ('id',sqlalchemy.Integer,primary_key = True),
                                 sqlalchemy.Column ('verification_result_id',sqlalchemy.Integer,sqlalchemy.ForeignKey('verification_result.id'),nullable=False),
                                 sqlalchemy.Column ('result',sqlalchemy.Enum(smtquery.solvers.solver.Verified),nullable=False),
                                 sqlalchemy.Column ('date', sqlalchemy.DateTime),
                                 )

        self._makesmt = lambda name,filepath,id: smtquery.intel.intels.getIntel (SMTFile(name,filepath,id))

    def makeSolverInterAction(self):
        self._solverInteraction = SolverInteraction()
        
    def initialise_db (self):
        with  smtquery.ui.output.makeProgressor () as progress:
        
            progress.message ("Initialising Database")
            self._meta.create_all (self._engine)

            with self._engine.connect () as conn:


                for bench in os.listdir (self._root):
                    benchpath = os.path.join (self._root,bench)
                    if not os.path.isdir (benchpath):
                        continue
                    bench_id = conn.execute (self._benchmark_table.insert ().values (name = bench)).inserted_primary_key[0]

                    for track in os.listdir (benchpath):
                        trackpath = os.path.join (benchpath,track)
                        if not os.path.isdir(trackpath):
                            continue
                        track_id = conn.execute (self._tracks_table.insert ().values (name = f"{bench}:{track}",
                                                                                bench_id = bench_id)).inserted_primary_key[0]

                        for instance in os.listdir (trackpath):
                            if not (instance.endswith (".smt") or instance.endswith (".smt2") or instance.endswith (".smt25")):
                                continue
                            instancepath = os.path.join (trackpath,instance)
                            dbvalues = {"name": f"{bench}:{track}:{instance}",
                                        "path": instancepath,
                                        "track_id": track_id}
                            progress.message (f"Initialising Database: {bench}:{track}:{instance}  ")

                            id = conn.execute (self._instance_table.insert ().values (
                                name = f"{bench}:{track}:{instance}",
                                path = instancepath[len(smtquery.config.getConfiguration().getCurrentWorkingDirectory())+1:],
                                track_id = track_id
                            )).inserted_primary_key[0]
                conn.commit ()
        
    def allocate_new_files_db (self):
        with  smtquery.ui.output.makeProgressor () as progress:
        
            progress.message ("Adding new files to the Database")
            self._meta.create_all (self._engine)
            with self._engine.connect () as conn:


                for bench in os.listdir (self._root):
                    benchpath = os.path.join (self._root,bench)
                    if not os.path.isdir (benchpath):
                        continue

                    # benchmark already added?
                    res = conn.execute (self._benchmark_table.select ().where ( self._benchmark_table.c.name == f"{bench}")).fetchall()
                    if len(res) > 0:
                        bench_id = res[0][0]
                    else:
                        bench_id = conn.execute (self._benchmark_table.insert ().values (name = bench)).inserted_primary_key[0]

                    for track in os.listdir (benchpath):
                        trackpath = os.path.join (benchpath,track)
                        if not os.path.isdir(trackpath):
                            continue

                        # track already added?
                        res = conn.execute (self._tracks_table.select ().where ( self._tracks_table.c.name == f"{bench}:{track}")).fetchall()
                        if len(res) > 0:
                            track_id = res[0][0]
                        else:
                            track_id = conn.execute (self._tracks_table.insert ().values (name = f"{bench}:{track}",
                                                                                bench_id = bench_id)).inserted_primary_key[0]

                        for instance in os.listdir (trackpath):
                            if not (instance.endswith (".smt") or instance.endswith (".smt2") or instance.endswith (".smt25")):
                                continue

                            # track already added?
                            res = conn.execute (self._instance_table.select ().where ( self._instance_table.c.name == f"{bench}:{track}:{instance}")).fetchall()
                            if len(res) > 0:
                                continue

                            print(f"Not found {bench}:{track}:{instance}")

                            instancepath = os.path.join (trackpath,instance)
                            dbvalues = {"name": f"{bench}:{track}:{instance}",
                                        "path": instancepath,
                                        "track_id": track_id}
                            progress.message (f"Adding to Database: {bench}:{track}:{instance}  ")

                            id = conn.execute (self._instance_table.insert ().values (
                                name = f"{bench}:{track}:{instance}",
                                path = instancepath[len(smtquery.config.getConfiguration().getCurrentWorkingDirectory())+1:],
                                track_id = track_id
                            )).inserted_primary_key[0]
                conn.commit ()

    def getBenchmarks (self):
        conn = self._engine.connect ()
        res = conn.execute (self._benchmark_table.select ())
        for row in res.fetchall ():
            yield Benchmark (row.name,self._engine,row.id,self._tracks_table,self._instance_table,self._makesmt)
    
    def searchFile (self,bench,track,file):
        with self._engine.connect () as conn:
            res = conn.execute (self._instance_table.select ().where ( self._instance_table.c.name == f"{bench}:{track}:{file}"))
            for row in res.fetchall ():
                return self._makesmt (row.name,row.path,row.id)
            return None

    def allFiles (self):
        with self._engine.connect () as conn:
            res = conn.execute (self._instance_table.select ())
            for row in res.fetchall ():
                yield self._makesmt (row.name,row.path,row.id)        
    
    def storeResult (self,result,smtfile,solver):
        with self._engine.connect () as conn:
            query = self._result_table.insert().values (
                instance_id = smtfile.getId (),
                result = result.getResult(),
                solver = solver.getName(),
                time = result.getTime(),
                model = result.getModel (),
                date = datetime.datetime.now ()
            ).returning (self._result_table.c.id)
            # busy wait for multiprocessing 
            while True:
                try:
                    res = conn.execute (query)
                    id = res.fetchone ()
                    conn.commit ()
                    return id[0]
                    break
                except Exception as e:
                    #print(f"{e} {os.getpid()} - I'm waiting... DB's locked!")
                    logging.getLogger ().error (f"storeResult: {e} {os.getpid()} - I'm waiting... DB's locked!")
                    time.sleep(1)   

    def storeResultDict (self,result,smtfile,solvername):
        with self._engine.connect () as conn:
            query = self._result_table.insert().values (
                instance_id = smtfile.getId (),
                result = result["result"],
                solver = solvername,
                time = result["time"],
                model = result["model"],
                date = datetime.datetime.now ()
            )

            # busy wait for multiprocessing 
            while True:
                try:
                    conn.execute (query)
                    conn.commit ()
                    break
                except Exception as e:
                    #print(f"{e} {os.getpid()} - I'm waiting... DB's locked!")
                    logging.getLogger ().error (f"storeResultDict: {e} {os.getpid()} - I'm waiting... DB's locked!")
                    time.sleep(1) 

    def storeVerified (self,result,verified):
        with self._engine.connect () as conn:
            query = self._validated_table.insert().values (
                verification_result_id = result["r_id"],
                result = verified,
                date = datetime.datetime.now ()
        )
            
            # busy wait for multiprocessing 
            while True:
                try:
                    conn.execute (query)
                    conn.commit ()
                    break
                except Exception as e:
                    #print(f"{e} {os.getpid()} - I'm waiting... DB's locked!")
                    logging.getLogger ().error (f"storeVerified: {e} {os.getpid()} - I'm waiting... DB's locked!")
                    time.sleep(1)    

    def storagePredicates (self):
        return smtquery.intel.intels.predicates ()

    def storageAttributes (self):
        return {
            "Name" : smtfile_getName,
            "Hash" : smtfile_hashContent,
            "Content" : smtfile_SMTString,            
        }

    # queries
    def _fetchResultsForBenchmarkIdFromDB(self,id,only_latest_results=True):
        with self._engine.connect () as conn:
            res = conn.execute (self._result_table.select ().where ( self._result_table.c.instance_id == id).order_by(self._result_table.c.date.desc()))
            results = dict()
            seen = set()
            for row in res.fetchall ():
                if only_latest_results:
                    if row.solver in seen:
                        continue
                    else:
                        seen.add(row.solver)

                # fetch verified
                verified = None
                v_res = conn.execute (self._validated_table.select ().where ( self._validated_table.c.verification_result_id == row.id).order_by(self._validated_table.c.date.desc()))
                v_results = v_res.fetchall()
                if len(v_results) > 0:
                    verified = v_results[0].result
                results[row.solver] = {"r_id" : row.id, "result" : row.result, "time" : row.time, "model" : row.model, "verified": verified}
            return results

    def _getResultIdForSolverBenchmark(self,id,solvername,only_latest_results=True):
        with self._engine.connect () as conn:
            res = conn.execute (self._result_table.select ().where ( self._result_table.c.instance_id == id and self._result_table.c.solver == solvername).order_by(self._result_table.c.date.desc()))
            for row in res.fetchall():
                return row[0]
            return None
        
    def getResultsForBenchmarkId(self,id):
        return self._fetchResultsForInstance(id)

    # use solver interaction to obtain results if they aren't present
    def getResultsForInstance(self,smtfile):
        results = self._solverInteraction.getResultsForInstance(smtfile)
        for solvername,res in results.items():
            if res["r_id"] == None:
                self.storeResultDict (res,smtfile,solvername)
                res["r_id"] = self._getResultIdForSolverBenchmark(smtfile.getId(),solvername)
                self.storeVerified (res,res["verified"])
        return results


    def getResultForSolver(self,smtfile,solvername):
        return self.getResultsForInstance(smtfile)[solvername] #self._solverInteraction.getResultForSolver(smtfile,solvername)





