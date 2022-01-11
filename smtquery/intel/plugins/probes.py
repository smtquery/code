import smtquery.smtcon.smt2expr
import smtquery.smtcon.exprfun
from smtquery.smtcon.expr import Kind
import smtquery.qlang.predicates
import os
import pickle
import tempfile
import smtquery.smtcon.smt2expr
from functools import partial



class Probes:
    def __init__(self):
        super().__init__ ()
        self._smtprobe = smtquery.smtcon.smt2expr.Z3SMTtoSExpr ()
        self._pickleBasePath = "smtquery/data/pickle"

    def _storeAST(self,smtfile,ast):
        rel_filepath = ''.join(f"/{f}" for f in smtfile.getName().split(":")[:-1])
        filename = smtfile.getName().split(":")[-1]
        pickle_file_path = f"{self._pickleBasePath}{rel_filepath}/{smtfile.hashContent()}_{filename}.pickle"
        with open(pickle_file_path, 'wb') as handle:
            pickle.dump(ast, handle, protocol=pickle.HIGHEST_PROTOCOL)

    def getAST(self,smtfile,filepath):
        rel_filepath = ''.join(f"/{f}" for f in smtfile.getName().split(":")[:-1])
        filename = smtfile.getName().split(":")[-1]
        pickle_file_path = f"{self._pickleBasePath}{rel_filepath}/{smtfile.hashContent()}_{smtfile.getName()}.pickle"

        if not os.path.exists(self._pickleBasePath+rel_filepath):
            os.makedirs(self._pickleBasePath+rel_filepath)

        if os.path.exists(pickle_file_path):
            with open(pickle_file_path, 'rb') as handle:
                return pickle.load(handle)
        else:
            pr = self._smtprobe.getAST (filepath)
            self._storeAST(smtfile,pr)
            return pr
        
    def getIntel (self, smtfile):
        with tempfile.TemporaryDirectory () as tmpdir:
            filepath = smtfile.copyOutSMTFile (tmpdir)
            pr = self.getAST(smtfile,filepath)
           
            # demo
            pr.add_intel_with_function(smtquery.smtcon.exprfun.HasAtom().apply,smtquery.smtcon.exprfun.HasAtom().merge,dict(),"has")

            # plot test
            if False:
                dot = graphviz.Digraph('G', format='pdf')
                pr.add_intel_with_function(smtquery.smtcon.exprfun.Plot().apply,smtquery.smtcon.exprfun.Plot().merge,{"dot" : dot, "succ" : [], "colours" : dict()},"plot")
                dot.render(smtfile.getName().replace(":","_"),cleanup=True)

            # variables
            pr.add_intel_with_function(smtquery.smtcon.exprfun.VariableCount().apply,smtquery.smtcon.exprfun.VariableCount().merge,dict(),"#variables")
            pr.add_intel_with_function(smtquery.smtcon.exprfun.VariableCountPath().apply,smtquery.smtcon.exprfun.VariableCountPath().merge,[],"pathVars")

            # variable Pie
            if False:
                dot = graphviz.Digraph('G', format='pdf')
                pie_data = {t : sum(x[1] for x in pr.get_intel()["#variables"][t].items()) for t in pr.get_intel()["#variables"].keys()}
                total_vars = sum(i for i in pie_data.values())

                import matplotlib.pyplot as plt
                labels = [t for t in pie_data.keys()]
                sizes = [(i/total_vars)*100 for i in pie_data.values()]
                explode = [0.15 if i == max(sizes) else 0 for i in sizes]
                fig1, ax1 = plt.subplots()
                ax1.pie(sizes, labels=labels, explode=explode, autopct='%1.1f%%',
                        shadow=True, startangle=90)
                ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
                plt.savefig(f'pie_{smtfile.getName().replace(":","_")}.pdf', format="pdf")

            return pr

    def predicates (self):
        return {
            "hasWEQ" : partial(hasKind,Kind.WEQ),
            "hasLinears" : partial(hasKind,Kind.LENGTH_CONSTRAINT),
            "hasRegex" : partial(hasKind,Kind.REGEX_CONSTRAINT)
        }

    @staticmethod
    def getName ():
        return "Probes"

    

    @staticmethod
    def getVersion ():
        return "0.0.1"
    
def hasKind(kind,smtfile):
    if kind in smtfile.Probes.get_intel()["has"]:
        return smtquery.qlang.predicates.Trool.TT
    else:
        return smtquery.qlang.predicates.Trool.FF 


def makePlugin ():
    return Probes
