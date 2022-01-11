
import smtquery.ui

class DummyPrinter:
    @staticmethod
    def getName ():
        return "DummyExtract"

    def __call__  (self,smtfile):
        with smtquery.ui.output.makePlainMessager () as mess:
            mess.message (smtfile)


def PullExtractor():
    return [DummyPrinter]
