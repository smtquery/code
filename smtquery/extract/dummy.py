
import smtquery.ui

class DummyPrinter:
    @staticmethod
    def getName ():
        return "DummyExtract"

    def finalise(self): 
        pass

    def __call__  (self,smtfile):
        with smtquery.ui.output.makePlainMessager () as mess:
            mess.message (smtfile.getName())


def PullExtractor():
    return [DummyPrinter]
