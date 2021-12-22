import sys

class Progresser:    
    def __enter__ (self):
        sys.stdout.write ("\n")
        return self
        
    def __exit__ (self,type,value,traceback):
        sys.stdout.write ("\n")

        
    def message (self,string):
        sys.stdout.write ("\r\u001b[0J{0}".format(string))

