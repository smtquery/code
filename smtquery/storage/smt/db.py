import os
import shutil
import sqlalchemy



meta = sqlalchemy.MetaData ()
        
benchmark_table  = sqlalchemy.Table ('benchmark',meta,
                               sqlalchemy.Column ('id',sqlalchemy.Integer,primary_key = True),
                               sqlalchemy.Column ('name',sqlalchemy.String (255),nullable = False)
                               )

tracks_table = sqlalchemy.Table ('track',meta,
                           sqlalchemy.Column ('id',sqlalchemy.Integer,primary_key = True),
                           sqlalchemy.Column ('name',sqlalchemy.String (255),nullable = False),
                        sqlalchemy.Column ('bench_id',sqlalchemy.Integer,sqlalchemy.ForeignKey('benchmark.id'),nullable=False)
                                 )

instance_table = sqlalchemy.Table ('instance', meta,
                             sqlalchemy.Column ('id',sqlalchemy.Integer,primary_key = True),
                             sqlalchemy.Column ('path',sqlalchemy.String(1024)),
                             sqlalchemy.Column ('name',sqlalchemy.String(255)),
                             sqlalchemy.Column ('track_id',sqlalchemy.Integer,sqlalchemy.ForeignKey('track.id'),nullable=False)
                                       )  
        

class SMTFile:
    def __init__(self,name,filepath):
        assert (os.path.exists(filepath))
        self._name = name
        self._filepath = filepath
        
        
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


class Track:
    def __init__ (self,name,engine,id):
        self._engine = engine
        self._id = id
        self._name = name

    def filesInTrack (self):
        conn = self._engine.connect ()
        res = conn.execute (instance_table.select().where (instance_table.c.track_id == self._id))
        for row in res.fetchall ():
            yield SMTFile (row.name,row.path)

    def getName (self):
        return self._name


class Benchmark:
    def __init__ (self,name,engine,id):
        self._engine = engine
        self._id = id
        self._name = name

    def tracksInBenchmark (self):
        conn = self._engine.connect ()
        res = conn.execute (tracks_table.select().where (tracks_table.c.bench_id == self._id))
        for row in res.fetchall ():
            yield Track (row.name,self._engine,row.id)
    

    def getName (self):
        return self._name

class DBFSStorage:
    def __init__ (self,root,enginestring):
        self._root = os.path.abspath(root)        
        self._engine = sqlalchemy.create_engine(enginestring)

    def initialise_db (self):
        meta.create_all (self._engine)

        conn = self._engine.connect ()
        
        
        for bench in os.listdir (self._root):
            benchpath = os.path.join (self._root,bench)
            if not os.path.isdir (benchpath):
                continue
            bench_id = conn.execute (benchmark_table.insert ().values (name = bench)).inserted_primary_key[0]
        
            for track in os.listdir (benchpath):
                trackpath = os.path.join (benchpath,track)
                if not os.path.isdir(trackpath):
                    continue
                track_id = conn.execute (tracks_table.insert ().values (name = f"{bench}:{track}",
                                                                        bench_id = bench_id)).inserted_primary_key[0]
            
                for instance in os.listdir (trackpath):
                    instancepath = os.path.join (trackpath,instance)
                    conn.execute (instance_table.insert ().values (name = f"{bench}:{track}:{instance}",
                                                                   path = instancepath,
                                                                   track_id = track_id)
                                  )
        
        
    def getBenchmarks (self):
        conn = self._engine.connect ()
        res = conn.execute (benchmark_table.select ())
        for row in res.fetchall ():
            yield Benchmark (row.name,self._engine,row.id)
        
    def searchFile (self,bench,track,file):
        conn = self._engine.connect ()
        res = conn.execute (instance_table.select ().where ( instance_table.c.name == f"{bench}:{track}:{file}"))
        for row in res.fetchall ():
            return SMTFile (row.name,row.path)
        return None
