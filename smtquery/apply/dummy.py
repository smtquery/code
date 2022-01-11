
import smtquery.ui

class DummyApply:
    @staticmethod
    def getName ():
        return "DummyApply"

    def __call__  (self,smtfile):
        return smtfile
    
def PullExtractor():
    return [DummyApply]
