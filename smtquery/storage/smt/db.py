import os
import shutil
import sqlalchemy
import datetime
import smtquery.solvers.solver
import hashlib

class SMTFile:
    def __init__(self,name,filepath,id):
        assert (os.path.exists(filepath))
        self._name = name
        self._filepath = filepath
        self._id = id
        
        
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
        conn = self._engine.connect ()
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
        conn = self._engine.connect ()
        res = conn.execute (self._tracks_table.select().where (self._tracks_table.c.bench_id == self._id))
        for row in res.fetchall ():
            yield Track (row.name,self._engine,row.id,self._instancetable,self._makesmt)
            
    def filesInBenchmark (self):
        conn = self._engine.connect ()
        res = conn.execute (self._instancetable.select().where (self._instancetable.c.track_id == self._id))
        for row in res.fetchall ():
             t = Track (row.name,self._engine,row.id,self._instancetable,self._makesmt)
             yield from t.filesInTrack ()
        
    def getName (self):
        return self._name



    
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
        self._intels = intels
        if intels:
            self._makesmt = lambda name,filepath,id: self._intels.getIntel (SMTFile(name,filepath,id))
        else:
            self._makesmt = SMTFile
        
    def initialise_db (self):
        self._meta.create_all (self._engine)

        conn = self._engine.connect ()
        
        
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
                    if not instance.endswith (".smt"):
                        continue
                    instancepath = os.path.join (trackpath,instance)
                    dbvalues = {"name": f"{bench}:{track}:{instance}",
                                "path": instancepath,
                                "track_id": track_id}
                    id = conn.execute (self._instance_table.insert ().values (
                        name = f"{bench}:{track}:{instance}",
                        path = instancepath,
                        track_id = track_id
                    )).inserted_primary_key[0]
                    
        
    def getBenchmarks (self):
        conn = self._engine.connect ()
        res = conn.execute (self._benchmark_table.select ())
        for row in res.fetchall ():
            yield Benchmark (row.name,self._engine,row.id,self._tracks_table,self._instance_table,self._makesmt)
    
    def searchFile (self,bench,track,file):
        conn = self._engine.connect ()
        res = conn.execute (self._instance_table.select ().where ( self._instance_table.c.name == f"{bench}:{track}:{file}"))
        for row in res.fetchall ():
            return self._makesmt (row.name,row.path,row.id)
        return None

    def allFiles (self):
        conn = self._engine.connect ()
        res = conn.execute (self._instance_table.select ())
        for row in res.fetchall ():
            yield self._makesmt (row.name,row.path,row.id)
        
    
    def storeResult (self,result,smtfile,solver):
        conn = self._engine.connect ()
        query = self._result_table.insert().values (
            instance_id = smtfile.getId (),
            result = result.getResult(),
            solver = solver.getName(),
            time = result.getTime(),
            model = result.getModel (),
            date = datetime.datetime.now ()
        )

        
        conn.execute (query)
        

    def storagePredicates (self):
        return self._intels.predicates ()

    def storageAttributes (self):
        return {
            "Name" : lambda smtfile: smtfile.getName (),
            "Hash" : lambda smtfile: smtfile.hashContent (),
            "Content" : lambda smtfile: smtfile.SMTString (),            
        }
