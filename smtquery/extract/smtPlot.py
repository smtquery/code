import smtquery.ui
from smtquery.smtcon.expr import *
import graphviz
import os

class SMTPlot:
    colours = dict()
    plot_output_folder = "output/plots"

    @staticmethod
    def getName ():
        return "SMTPlot"

    def finalise(self,total): 
        pass

    def __call__  (self,smtfile):
        with smtquery.ui.output.makePlainMessager () as mess:
            mess.message (smtfile.getName())
            self.colours = dict()
            ast = smtfile.Probes._get()
            dot = graphviz.Digraph('G', format='pdf')
            self._buildGraph(ast,dot)
            dot.render(self._getOutputFileName(smtfile.getName()),cleanup=True)


    def _buildGraph(self,ast,dot):
        for a in ast:
            dot = self._buildAssert(a,dot)
        return dot

    def _buildAssert(self,expr,dot):
        label = expr.decl()
        if expr.is_variable() or expr.is_const():
            label = f"{expr}"
        if label not in self.colours:
            self.colours[label] = self._getNewColour([self.colours[l] for l in self.colours])
        dot.node(name=f"{expr.id()}", label=f"{label}", style='filled,rounded', shape="rectangle", color=f"{self.colours[label][0]}", fontcolor=f"{self.colours[label][1]}")
        for c in expr.children():
            dot = self._buildAssert(c,dot)
            dot.edge(f"{expr.id()}", f"{c.id()}",penwidth="0.5",arrowhead="none")
        return dot

    # auxilary functions
    def _colourGen(self):
        import random
        r = lambda: random.randint(0,255)
        c_r,c_g,c_b = r(),r(),r()
        colourGen = lambda : '#%02X%02X%02X' % (c_r,c_g,c_b)
        textColour = "#000000" if ((c_r * 0.299) + (c_g * 0.587) + (c_b * 0.114)) > 186 else "#FFFFFF"
        return (colourGen(),textColour)

    def _getNewColour(self,colours):
        while True:
            newColour = self._colourGen()
            if newColour not in colours:
                return newColour

    def _getOutputFileName(self,smtfileName):
        rel_filepath = ''.join(f"/{f}" for f in smtfileName.split(":")[:-1])
        filename = smtfileName.split(":")[-1]
        file_path = f"{self.plot_output_folder}/{rel_filepath}/{filename}"

        if not os.path.exists(self.plot_output_folder+rel_filepath):
            os.makedirs(self.plot_output_folder+rel_filepath)

        return file_path

def PullExtractor():
    return [SMTPlot]
