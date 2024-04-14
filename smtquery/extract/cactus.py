import smtquery.ui
from smtquery.solvers.solver import *
import time
import statistics

class CactusPlot:
    output_folder = "./output/cactus/"

    # data for accumulation
    _maxPoints = 100
    _startPoints = 0
    tikz = False

    @staticmethod
    def getName ():
        return "CactusPlot"

    def finalise(self,results,total):
        self._generateCactus(self._generateCactusData(results),self.output_folder,self.tikz)
        
    def __call__  (self,smtfile):
        # collect results
        _storage = smtquery.config.getConfiguration().getStorage ()
        b_input = smtfile.getName().split(":")
        b_smtfile = _storage.searchFile(b_input[0],b_input[1],b_input[2])
        results = dict()
        if b_smtfile != None:
            b_id = b_smtfile.getId() 
            res = _storage.getResultsForInstance(smtfile)
            for s in res.keys():
                if s not in results:
                    results[s] = []
                if res[s]["result"] in [Result.NotSatisfied,Result.Satisfied]:
                    results[s]+=[(b_id,res[s]["time"])]
        return results

    def _generateCactusData(self,results):
        t_results = dict()
        for d in results:
            if d != None:
                for s,entries in d.items():
                    if s not in t_results:
                        t_results[s] = []
                    t_results[s]+=entries
        results = {s : sorted(t_results[s], key=lambda r:r[1]) for s in t_results.keys()}
        cactus_data = dict()
        for s in results.keys():
            t_time = 0
            cactus_data[s] = []
            for i,r in enumerate(results[s]):
                t_time+=r[1]
                cactus_data[s]+=[{"x" : i, "instance" : r[0], "time" : r[1], "y" : t_time }]
        return cactus_data

    def _generateCactus(self,cactus_data,file_path,tikz):
        colours = dict()
        for s in cactus_data.keys():
            colours[s] = self._getNewColour([c for c in colours.values()])

        if not tikz:
            self._genPDFCactus(cactus_data,file_path,colours)
        else:
            self._genTIKZCactus(cactus_data,file_path,colours)

    # PDF
    def _genPDFCactus(self,cactus_data,file_path,colours):
        from matplotlib.figure import Figure
        from matplotlib.font_manager import FontProperties
        from io import BytesIO

        start_at = 0
        fig = Figure(figsize=(6,3))
        ax = fig.subplots()
        fontP = FontProperties()
        fontP.set_size('small')
        lgd = None
    
        for s in cactus_data.keys():
            sColour = colours[s][0]
            data = [i[1] for i in self._accumulatePoints(cactus_data[s]) if i[0] >= start_at]
            ax.plot (range(start_at,len(data)+start_at),data,'-',linewidth=2.5,label=s,color=sColour)
            ax.fill_between(range(start_at,len(data)+start_at),data, color=sColour,alpha=0.15)
            lgd = ax.legend(fancybox=True,bbox_to_anchor=(0., 1.02, 1., .102), loc='lower left', ncol=2, mode="expand", borderaxespad=0.,frameon=False)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['bottom'].set_visible(False)
            ax.spines['left'].set_visible(False)
            ax.yaxis.grid(color='black', linestyle='dashdot', linewidth=0.1)
            
            # Save it to a temporary buffer.
            buf = BytesIO()

        os.makedirs(file_path,exist_ok = True)
        if lgd == None:
            return
        fig.savefig(f"{file_path}/cactus_{int(time.time())}.pdf",format="pdf",dpi=320,bbox_extra_artists=(lgd,), bbox_inches='tight')


    # Tikz
    def _genTIKZBody(self,cactus_data,colours):
        latex_str = self._genLatexColours(colours)
        latex_str += self.genTableHeader()
        for s in cactus_data.keys():
            fillbetween = []
            data = self._accumulatePoints(cactus_data[s])
            sColour = colours[s][0]
            if (len(cactus_data) > 0):                
                output = ('\n\\addplot[name path=path'+str(s.replace('_','').replace('.',''))+' , colour'+str(s.replace('_','').replace('.',''))+', line width=1.5pt, solid] coordinates {')

                for (x,y) in data:
                    output+="("+str(x)+","+str(y)+")"
                output+= '};\n'

                # collect data to fill between curve and x axis; needs to be placed in the end 
                # Needs Packages:
                # \usepackage{pgfplots}
                # \usepgfplotslibrary{fillbetween}
                fillbetween+=['\\path[name path=axis'+str(s.replace('_','').replace('.',''))+'] (axis cs:0,0) -- (axis cs:'+str(data[len(data)-1][0])+',0);\n']
                fillbetween+=['\\addplot [thick,color=colour'+str(s.replace('_','').replace('.',''))+',fill=colour'+str(s.replace('_','').replace('.',''))+',fill opacity=0.1] fill between [of=path'+str(s.replace('_','').replace('.',''))+' and axis'+str(s.replace('_','').replace('.',''))+'];\n']


                output+='\\addlegendentry{'+str(s)+'}\n'
                output+='\n'
                latex_str+=output

                for l in fillbetween:
                    latex_str+=l

        latex_str+=self.genTableFooter()
        return latex_str

    def genTableHeader (self):
        return'''\\begin{figure}[t!]
\\resizebox{.95\\textwidth}{!}{\\pgfplotsset{scaled x ticks=false}\\pgfplotsset{scaled y ticks=false}\\begin{tikzpicture}\\begin{axis}[title=Total,xlabel=Solved instances,ylabel=Time (seconds),,legend columns=2,legend style={nodes={scale=0.5, transform shape}, fill=none,anchor=east,align=center },axis line style={draw=none}, xtick pos=left, ytick pos=left, ymajorgrids=true, legend style={draw=none},x post scale=2,y post scale=1]'''

    def genTableFooter (self):
        return '''\\end{axis}\\end{tikzpicture}}\n\n
\\caption{Cactus plot summarizing performance.}
\\label{fig:cactus}

\\end{figure}'''

    def _genLatexColours(self,colours):
        latex_str = ""
        for s in colours.keys():
            latex_str+= """\\definecolor{colour"""+str(s.replace('_','').replace('.',''))+"""}{HTML}{"""+str(colours[s][0][1:])+"""}\n"""
        return latex_str
    
    def _genTIKZCactus(self,cactus_data,file_path,colours):
        latex_str = self.genLatexDocumentHead()
        latex_str += self._genTIKZBody (cactus_data,colours)
        latex_str += self.genLatexDocumentFoot()

        with open(f"{file_path}/cactus_{int(time.time())}.tex", "w") as text_file:
            text_file.write(latex_str)

    def genLatexDocumentHead(self):
        return '''\\documentclass[11pt]{article}
\\usepackage{color}
\\usepackage{tikz}
\\usepackage{pgfplots}
\\usepgfplotslibrary{fillbetween}
\\pgfplotsset{compat=1.16}
\\begin{document}
'''

    def genLatexDocumentFoot(self):
        return '''\\end{document}'''


    ## aux
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
            
    def _accumulatePoints(self,l):
        if len(l) < self._maxPoints:
            ll = [(i["x"],i["y"]) for i in l]
        else:
            ll = []
            total_points = len(l)

            accumulation_count = round((total_points-self._startPoints)/(self._maxPoints-2))
            i = self._startPoints+1
            j = 1
            ll.append((self._startPoints+1,l[self._startPoints]["y"]))
            while True:
                if j*accumulation_count+1 < (total_points-self._startPoints):
                    x = statistics.mean([value["x"] for value in l[i:self._startPoints+(accumulation_count*j+1)]])
                    y = statistics.mean([value["y"] for value in l[i:self._startPoints+(accumulation_count*j+1)]])
                    ll.append((x,y))
                    i=accumulation_count+i 
                else: 
                    if i < ((total_points-self._startPoints)-1):

                        x = statistics.mean([value["x"] for value in l[i:total_points-1]])
                        y = statistics.mean([value["y"] for value in l[i:total_points-1]])
                        ll.append((x,y))
                    break
                j+=1
            ll.append((total_points,l[total_points-1]["y"]))

        return ll


class PDFCactusPlot(CactusPlot):
    tikz = False
    @staticmethod
    def getName ():
        return "CactusPlot"
    
class LatexCactusPlot(CactusPlot):
    tikz = True
    @staticmethod
    def getName ():
        return "LatexCactusPlot"


def PullExtractor():
    return [PDFCactusPlot,LatexCactusPlot]
