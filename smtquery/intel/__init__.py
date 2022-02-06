from smtquery.intel.manager import Manager
from smtquery.intel.plugins import plugins

intels =  Manager ()

def makeIntelManager (pluginnames): 
    global intels
    intels = Manager ()
    for p in pluginnames:
        if p in plugins:
            intels.addPlugin (plugins[p] ())
        else:
            raise f"No plugin named {p}"

    
