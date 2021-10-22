import os
import shutil
import sqlalchemy
import z3


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
                             sqlalchemy.Column ('track_id',sqlalchemy.Integer,sqlalchemy.ForeignKey('track.id'),nullable=False),
                             sqlalchemy.Column ('weq',sqlalchemy.Integer),
                             sqlalchemy.Column ('length',sqlalchemy.Integer),
                             sqlalchemy.Column ('regex',sqlalchemy.Integer),
                             sqlalchemy.Column ('At',sqlalchemy.Integer),
                             sqlalchemy.Column ('str.substr',sqlalchemy.Integer),
                             sqlalchemy.Column ('PrefixOf',sqlalchemy.Integer),
                             sqlalchemy.Column ('SuffixOf',sqlalchemy.Integer),
                             sqlalchemy.Column ('Contains',sqlalchemy.Integer),
                             sqlalchemy.Column ('IndexOf',sqlalchemy.Integer),
                             sqlalchemy.Column ('Replace',sqlalchemy.Integer),
                             sqlalchemy.Column ('IntToStr',sqlalchemy.Integer),
                             sqlalchemy.Column ('StrToInt',sqlalchemy.Integer)
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

class ProbeSMTFiles():
    hofunc = ["At","str.substr","PrefixOf","SuffixOf","Contains","IndexOf","Replace","IntToStr","StrToInt"]
    def __init__(self):
        self.s = z3.Solver()

    def getZ3AST(self,instance_path):
        return z3.parse_smt2_file(instance_path)

    def _mergeData(self,d1,d2):
        for k in set(d1.keys()).union(set(d2.keys())):
            if k in d1 and k in d2:
                if isinstance(d1[k],int): 
                    d1[k] = d1[k]+d2[k]
                else:
                    d1[k] = self._mergeData(d1[k],d2[k])
            elif k in d2:
                d1[k] = d2[k]
        return d1
    
    def traverseAst(self,ast):
        data = {"variables": dict(), "weq":0,"length":0,"regex":0,"hof":{f : 0 for f in self.hofunc}}
        if type(ast) in [z3.z3.AstVector]:
            for x in ast:
                data = self._mergeData(data,self.traverseAst(x))
        else:
            children = ast.children()
            if len(children) == 0:
                if str(ast.sort()) == "String":
                    if not ast.is_string_value():
                        x = str(ast)
                        if x not in data["variables"]:
                            data["variables"][x] = 0
                        data["variables"][x]+=1
                return data
            op = ast.decl()
            if str(op) == "InRe":
                data["regex"]+=1
            elif str(op) in self.hofunc:
                data["hof"][str(op)]+=1
            if type(ast) == z3.z3.BoolRef and len(children) == 2 and str(children[0].sort()) == "String" and children[0].sort() == children[1].sort():
                data["weq"]+=1
            elif type(ast) == z3.z3.BoolRef and len(children) == 2 and str(children[0].sort()) == "Int" and children[0].sort() == children[1].sort():
                data["length"]+=1

            for x in children:
                data = self._mergeData(data,self.traverseAst(x))
        return data

    def processInstance(self,path):
        return self.traverseAst(self.getZ3AST(path))

class DBFSStorage:
    def __init__ (self,root,enginestring):
        self._root = os.path.abspath(root)        
        self._engine = sqlalchemy.create_engine(enginestring)
        self._smtProbe = ProbeSMTFiles()

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
                    dbvalues = {"name": f"{bench}:{track}:{instance}",
                                "path": instancepath,
                                "track_id": track_id}
                    instancedata = self._smtProbe.processInstance(instancepath)
                    for k in instancedata.keys():
                        if isinstance(instancedata[k],int):
                            dbvalues[k] = instancedata[k]
                        elif isinstance(instancedata[k],dict):
                            for kk in instancedata[k].keys():
                                dbvalues[kk] = instancedata[k][kk]
                    conn.execute (instance_table.insert ().values ([dbvalues]))
        
        
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