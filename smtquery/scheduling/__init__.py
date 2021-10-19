
import smtquery.scheduling.multi
import smtquery.scheduling.celerys
import yaml

def createFrontScheduler (filelocator):
    conffile = filelocator.findFile ("scheduling.yml")
    if conffile:
        with open (conffile,'r') as ff:
            data = yaml.load (ff,Loader=yaml.Loader)
            if data["scheduler"]["name"] == "multiprocessing":
                return smtquery.scheduling.multi.Queue (int(data["scheduler"]["cores"]))        
            if data["scheduler"]["name"] == "celery":
                return smtquery.scheduling.celerys.Queue ("HH")


