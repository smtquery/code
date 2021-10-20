import yaml
import smtquery.storage.smt.fs
import smtquery.storage.smt.db


storage = None

def createStorage (filelocator):
    conffile = filelocator.findFile ("storage.yml")
    global storage
    if conffile:
        with open (conffile,'r') as ff:
            data = yaml.load (ff,Loader=yaml.Loader)
            if data["SMTStore"]["name"] == "FS":
                storage = smtquery.storage.smt.fs.SMTStorage (data["SMTStore"]["root"])
            if data["SMTStore"]["name"] == "DBFS":
                storage = smtquery.storage.smt.db.DBFSStorage (data["SMTStore"]["root"],
                                                               data["SMTStore"]["engine_string"]
                                                              )
    return storage
