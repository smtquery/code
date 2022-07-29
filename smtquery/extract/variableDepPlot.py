import smtquery.ui
from smtquery.smtcon.expr import *
import graphviz
import os
from smtquery.intel.plugins.probes import Probes

class VariableDependencyPlot:
    colours = dict()
    plot_output_folder = "output/vardep"

    @staticmethod
    def getName ():
        return "VarDepPlot"

    def finalise(self,results,total): 
        pass

    def __call__  (self,smtfile):
        with smtquery.ui.output.makePlainMessager () as mess:
            mess.message (smtfile.getName())
            self.colours = dict()
            ast = Probes().getIntel(smtfile)
            dot = graphviz.Digraph('G', format='pdf')
            self._buildGraph(ast,dot)
            dot.render(self._getOutputFileName(smtfile.getName()),cleanup=True)


    def _buildGraph(self,ast,dot):
        for t in ast.get_intel()["variables"].keys():
            for x in ast.get_intel()["variables"][t]: #[var for var in ast.get_intel()["#variables"][t].keys() if ast.get_intel()["#variables"][t][var] > 0]:
                if x not in self.colours:
                    self.colours[x] = self._getNewColour([self.colours[l] for l in self.colours])
                dot.node(name=f"{x}", label=f"{x}", style='filled,rounded', shape="rectangle", color=f"{self.colours[x][0]}", fontcolor=f"{self.colours[x][1]}")

        for expr in ast:
            label = expr.id()
            if expr.is_variable() or expr.is_const():
                continue
            if label not in self.colours:
                self.colours[label] = self._getNewColour([self.colours[l] for l in self.colours])
            dot.node(name=f"{label}", label=f"{self._shortenText(str(expr))}", style='filled,rounded', shape="rectangle", color=f"{self.colours[label][0]}", fontcolor=f"{self.colours[label][1]}")

            for t in expr.get_intel()["variables"].keys():
                for x in expr.get_intel()["variables"][t]: #[var for var in expr.get_intel()["#variables"][t].keys() if expr.get_intel()["#variables"][t][var] > 0]:
                    dot.edge(f"{x}", f"{label}",penwidth="0.5",arrowhead="none")
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


    def _shortenText(self,text):
        if len(text) > 20:
            return text[:20]+"..."
        return text

    def _getOutputFileName(self,smtfileName):
        rel_filepath = ''.join(f"/{f}" for f in smtfileName.split(":")[:-1])
        filename = smtfileName.split(":")[-1]
        file_path = f"{self.plot_output_folder}/{rel_filepath}/{filename}"

        if not os.path.exists(self.plot_output_folder+rel_filepath):
            try:
                os.makedirs(self.plot_output_folder+rel_filepath)
            except Exception as e:
                pass # already created due to multiprocessing

        return file_path

def PullExtractor():
    return [VariableDependencyPlot]
