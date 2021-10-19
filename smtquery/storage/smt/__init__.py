import yaml
import smtquery.storage.smt.fs

def createStorage (filelocator):
    conffile = filelocator.findFile ("storage.yml")
    solverarr = {}
    if conffile:
        with open (conffile,'r') as ff:
            data = yaml.load (ff,Loader=yaml.Loader)
            if data["SMTStore"]["name"] == "FS":
                return smtquery.storage.smt.fs.SMTStorage (data["SMTStore"]["root"])
    
