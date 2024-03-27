import smtquery.ui
import smtquery.storage.smt.fs
import smtquery.intel


from smtquery.smtcon.expr import *
from smtquery.smtcon.exprfun import *
from smtquery.intel.plugins.probes import Probes


class RestrictConstraints:
    output_folder = "output/restrict_constraints"
    root = "."
    required_intel = [smtquery.smtcon.exprfun.HasAtom]

    def __call__  (self,smtfile,collect_kinds):
        #collect_kinds = [Kind.LENGTH_CONSTRAINT,Kind.WEQ] #[Kind.REGEX_CONSTRAINT,Kind.WEQ]
        new_ast = ASTRef()
        p = Probes()
        ast = p.getIntel(smtfile,self.required_intel)
        for ass in ast:
            new_ass_list = []
            if ass.kind() == Kind.WEQ and ass.kind() in collect_kinds:
                new_ass_list = self._processWEQ(ass,p)
            elif ass.kind() == Kind.REGEX_CONSTRAINT and ass.kind() in collect_kinds:
                new_ass_list = self._processRegEx(ass,p)
            elif ass.kind() == Kind.LENGTH_CONSTRAINT and ass.kind() in collect_kinds:
                new_ass_list = self._processLength(ass,p)
            elif ass.kind() == Kind.OTHER and ass.sort() == Sort.Bool:
                new_ass_list = self._processBool(ass,collect_kinds,p)
            if len(new_ass_list) == 1:
                new_ast.add_node(new_ass_list[0])
        with smtquery.ui.output.makeFile(self._getOutputFilePath(smtfile)) as handle:
            handle.write(str(new_ast))
        new_smtfile = smtquery.storage.smt.fs.SMTFile(smtfile.getName(),self.root+"/"+self._getOutputFilePath(smtfile))
        p.getIntel(new_smtfile,self.required_intel)
        
        return new_smtfile
    
    def _processWEQ(self,expr,p):
        if set(expr.intel[p.getIntelKey2Class(self.required_intel[0])].keys()).issubset({Kind.CONSTANT,Kind.VARIABLE,Kind.WEQ,Kind.OTHER}):
            expr.reset_intel()
            return [expr]
        return []

    def _processRegEx(self,expr,p):
        return [expr]

    def _processLength(self,expr,p):
        if set(expr.intel[p.getIntelKey2Class(self.required_intel[0])].keys()).issubset({Kind.CONSTANT,Kind.VARIABLE,Kind.LENGTH_CONSTRAINT,Kind.OTHER}):
            expr.reset_intel()
            return [expr]
        return []

    def _processBool(self,expr,collect_kinds,p):
        new_kids = []
        for c in expr.children():
            if c.kind() == Kind.WEQ and c.kind() in collect_kinds:
                kid = self._processWEQ(c,p)
                if len(kid) >= 1:
                    new_kids+=kid
            elif c.kind() == Kind.REGEX_CONSTRAINT and c.kind() in collect_kinds:
                kid = self._processRegEx(c,p)
                if len(kid) >= 1:
                    new_kids+=kid
            elif c.kind() == Kind.LENGTH_CONSTRAINT and c.kind() in collect_kinds:
                kid = self._processLength(c,p)
                if len(kid) >= 1:
                    new_kids+=kid 
            elif c.kind() == Kind.OTHER and c.sort() == Sort.Bool:
                new_kids+=self._processBool(c,collect_kinds,p)
            # special case for the condition of ite
            elif expr.decl() == "ite" and expr.children()[0] == c and c.sort() == Sort.Bool:
                new_kids+=[c]     
        if new_kids == None or len(new_kids) == 0:
            return []
        elif len(new_kids) == 1:
            return [new_kids[0]]
        else:
            expr.vChildren = new_kids
            return [expr]

    def _getOutputFilePath(self,smtfile):
        return self.output_folder+''.join(f"/{f}" for f in smtfile.getName().split(":"))

class Restrict2WEQ:
    @staticmethod
    def getName ():
        return "Restrict2WEQ"

    def __call__  (self,smtfile):
        return RestrictConstraints()(smtfile,[Kind.WEQ])
        
class Restrict2Length:
    @staticmethod
    def getName ():
        return "Restrict2Length"

    def __call__  (self,smtfile):
        return RestrictConstraints()(smtfile,[Kind.LENGTH_CONSTRAINT])

class Restrict2RegEx:
    @staticmethod
    def getName ():
        return "Restrict2RegEx"

    def __call__  (self,smtfile):
        return RestrictConstraints()(smtfile,[Kind.REGEX_CONSTRAINT])       


def PullExtractor():
    return [Restrict2WEQ,Restrict2Length,Restrict2RegEx]
