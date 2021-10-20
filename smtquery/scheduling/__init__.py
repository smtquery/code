
import smtquery.scheduling.multi
import smtquery.scheduling.celerys
import yaml

scheduler  = None

def createFrontScheduler (filelocator):
    global scheduler
    conffile = filelocator.findFile ("scheduling.yml")
    if conffile:
        with open (conffile,'r') as ff:
            data = yaml.load (ff,Loader=yaml.Loader)
            if data["scheduler"]["name"] == "multiprocessing":
                scheduler = smtquery.scheduling.multi.Queue (int(data["scheduler"]["cores"]))        
            if data["scheduler"]["name"] == "celery":
                scheduler = smtquery.scheduling.celerys.Queue ("HH")
                

