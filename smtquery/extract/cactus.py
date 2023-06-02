import smtquery.ui
from smtquery.solvers.solver import *

class CactusPlot:
    output_folder = "./output/cactus/"

    @staticmethod
    def getName ():
        return "CactusPlot"

    def finalise(self,results,total):
        self._generateCactus(self._generateCactusData(results),self.output_folder)
        
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

        #with smtquery.ui.output.makePlainMessager () as mess:
        #    mess.message (smtfile.getName())

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

    def _generateCactus(self,cactus_data,file_path):
        from matplotlib.figure import Figure
        from matplotlib.font_manager import FontProperties
        from io import BytesIO

        start_at = 0
        fig = Figure(figsize=(6,3))
        ax = fig.subplots()
        fontP = FontProperties()
        fontP.set_size('small')

        colours = dict()
        for s in cactus_data.keys():
            colours[s] = self._getNewColour([c for c in colours.values()])

        for s in cactus_data.keys():
            sColour = colours[s][0]
            data = [i["y"] for i in cactus_data[s] if i["x"] >= start_at]
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
        fig.savefig(f"{file_path}/cactus.pdf",format="pdf",dpi=320,bbox_extra_artists=(lgd,), bbox_inches='tight')

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


def PullExtractor():
    return [CactusPlot]
