import sqlalchemy
import smtquery.storage.smt.db
db = "sqlite:///db.sql"
storage = smtquery.storage.smt.db.DBFSStorage ("./data/smtfiles",db)

import smtquery.intel


storage.initialise_db()


for bench in storage.getBenchmarks ():
    for track in bench.tracksInBenchmark ():
        for instance in track.filesInTrack ():
            print (instance.getName ())
        

