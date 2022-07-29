import smtquery.ui
from smtquery.solvers.solver import *

class MatchingPie:
    _matchingCount = 0
    output_folder = "./output/pie/"

    @staticmethod
    def getName ():
        return "MatchingPie"

    def finalise(self,results,total):
        matchingCount = sum([r  for r in results if r != None])
        self._generatePie({f"rest ({total-matchingCount} instances)" : total-matchingCount, f"matching ({matchingCount} instances)" : matchingCount})

    def __call__  (self,smtfile):
        return 1

    def _generatePie(self,pie_data):
        import os
        import matplotlib.pyplot as plt
        colours = []
        while len(colours) < 2:
            colours+=[self._getNewColour(colours)]

        total_vars = sum(i for i in pie_data.values())
        labels = [t for t in pie_data.keys()]
        sizes = [(i/total_vars)*100 for i in pie_data.values()]
        explode = [0.15 if i == max(sizes) else 0 for i in sizes]
        fig1, ax1 = plt.subplots()
        ax1.pie(sizes, labels=labels, autopct='%1.1f%%',
                shadow=False, startangle=90,colors=[c[0] for c in colours]) # explode=explode, 

        centre_circle = plt.Circle((0,0),0.80,fc='white')
        fig = plt.gcf()
        fig.gca().add_artist(centre_circle)


        ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
        os.makedirs(self.output_folder,exist_ok = True)
        plt.savefig(f'{self.output_folder}/pie.pdf', format="pdf")

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
    return [MatchingPie]
