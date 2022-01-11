from smtquery.intel.manager import Manager
from smtquery.intel.plugins import plugins
manager = Manager ()





def makeIntelManager (pluginnames): 
    global manager
    manager = Manager ()
    for p in pluginnames:
        if p in plugins:
            manager.addPlugin (plugins[p] ())
        else:
            raise f"No plugin named {p}"
    return manager
    
