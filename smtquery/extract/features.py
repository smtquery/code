import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier

import smtquery.ui
from smtquery.solvers.solver import *
from automata.fa.dfa import DFA
from smtquery.intel.plugins.probes import Probes

from smtquery.extract.featureExtractionFiles import newParse

from smtquery.extract.featureExtractionFiles import extractFeatWE


import graphviz
from sklearn import tree
from dtreeviz.trees import dtreeviz

import smtquery.config

class Features:
    def __init__(self):
        pass
        
    def create_report(self, dataframe, benchmarkName):
        report = "Report for Benchmark: " + benchmarkName + " with " + str(len(dataframe.index)) + " instances \n"
        report = report + "\n"

        columns = dataframe.columns
        for column in columns[:-2]:
            report = report + column + " "
            avgc = dataframe[column].mean()
            avgStr = dataframe.loc[dataframe['solver'] == 1, column].mean()
            avgSeq = dataframe.loc[dataframe['solver'] == 0, column].mean()
            avgCvc = dataframe.loc[dataframe['solver'] == 2, column].mean()
            report = report + f"Average: {avgc}"
            for i,s in enumerate(self._solvers):
                mean = avgStr = dataframe.loc[dataframe['solver'] == i, column].mean()
                
                report += f" Average for {s}: {mean}"
            report += "\n"
            notSolved = len(dataframe.index) - len(dataframe.dropna().index)
            #report = report + "\n"
            #report = report + "Number of not solvable instances: " + str(notSolved) + "\n"
            #report = report + "Instances solved by Z3Str3: " + str(len(dataframe[dataframe['solver'] == 1])) + "\n"
#            report = report + "Instances solved by Z3Seq: " + str(len(dataframe[dataframe['solver'] == 0])) + "\n"
            #report = report + "Instances solved by CVC5: " + str(len(dataframe[dataframe['solver'] == 2])) + "\n"
        return report



    def trainAndTestDTC(self, dtc, data, Y, crit, depth, feat, split):
        y = Y.values.ravel()
        X = data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=0)
        dtc.criterion = crit
        dtc.max_depth = depth
        dtc.max_features = feat
        dtc.splitter = split
        dtc.fit(X_train, y_train)

        viz = dtreeviz(dtc, X_train, y_train,
                      target_name="target",
                      feature_names=["numStringVar", "varRatio", "numWEQ", "numQWEQ", "maxNumOfQVar", "scopeIncidence",
                     "largesRatioVarCon", "smallestRatioVarCon", "largestRatioLR", "smallestRatioLR",
                     "numReg", "maxSymb", "maxDepth", "maxNumState", "numLin", "numAsserts",
                     "maxRecDepth"],
                     #class_names=['Z3Seq', 'Z3Str3','CVC5'])
                     class_names=self._solvers
                       )
        return viz



    def buildTree(self, data):
        # Parameter for Decision Tree
        criterion = 'gini'
        max_d = 10
        max_f = None
        splitter = 'best'
        Y = data.iloc[:, 17]
        data = data.iloc[:, :17]
        dtc = DecisionTreeClassifier()
        return self.trainAndTestDTC(dtc, data, Y, criterion, max_d, max_f, splitter)

    @staticmethod
    def getName():
        return "Features"

    def finalise(self, results, total):
        self._output_folder = os.path.join(smtquery.config.getConfiguration ().getOutputLocation (),"Features")
        self._solvers = list(smtquery.config.getConfiguration().getSolvers().keys ())
        
        dataframe = pd.DataFrame(
            columns=["numStringVar", "varRatio", "numWEQ", "numQWEQ", "maxNumOfQVar", "scopeIncidence",
                     "largesRatioVarCon", "smallestRatioVarCon", "largestRatioLR", "smallestRatioLR",
                     "numReg", "maxSymb", "maxDepth", "maxNumState", "numLin", "numAsserts",
                     "maxRecDepth", "solver", "path"], data=results)

        path = os.path.join (self._output_folder,dataframe["path"][0].split(":")[0])
        os.makedirs(path, exist_ok=True)
        dataframe.to_csv(os.path.join (path,"features.csv"), index=False)

        df = dataframe
        viz = self.buildTree(df.dropna())
        viz.save(os.path.join (path,"decisionTree.svg"))

        report = self.create_report(dataframe, dataframe["path"][0].split(":")[0])
        with open(f"{path}/report.txt", 'w') as f:
            f.write(report)
        f.close()

    def __call__(self, smtfile):
        _storage = smtquery.config.getConfiguration().getStorage()
        ast = Probes().getIntel(smtfile)
        allVar, StringVar, WEQ, RGX, numLin, numasserts, recDepth, RGXdepths = newParse.extract(ast)
        alphabets = []
        minDafStates = []
        for nfa in RGX:
            alphabets.append(len(nfa.input_symbols))
            dfa = DFA.from_nfa(nfa).minify()
            minDafStates.append(len(dfa.states))

        maxDepth = 0
        if len(RGXdepths) > 0:
            maxDepth = max(RGXdepths)
        maxSymb = 0
        if len(alphabets) > 0:
            maxSymb = max(alphabets)
        maxNumState = 0
        if len(minDafStates) > 0: 
            maxNumState = max(minDafStates)

        numStringVar = len(StringVar)
        if len(allVar) == 0:
            varRatio = 0
        else:
            varRatio = numStringVar / len(allVar)
        numWEQ = len(WEQ)
        numReg = len(RGX)
        numQWEQ, maxNumOfQVar, scopeIncidence, largesRatioVarCon, smallestRatioVarCon, largestRatioLR, smallestRatioLR = extractFeatWE.extractFeatures(
            WEQ, StringVar)

        if smallestRatioLR == 10000:
            smallestRatioLR = 0
        if smallestRatioVarCon == 10000:
            smallestRatioVarCon = 0
        res = _storage.getResultsForInstance(smtfile)
        solverindex = 0
        solvertime = 1000
        for i,s in enumerate(self._solvers):
            if res[s]["result"] in [Result.NotSatisfied, Result.Satisfied]:
                if res[s]["time"] < solvertime:
                    solvertime = res[s]["time"]
                    solverindex = i

        name = smtfile.getName()
        s_row = [numStringVar, varRatio, numWEQ, numQWEQ, maxNumOfQVar, scopeIncidence, largesRatioVarCon,
                 smallestRatioVarCon, largestRatioLR, smallestRatioLR, numReg, maxSymb, maxDepth, maxNumState, numLin,
                 numasserts, recDepth, solverindex, name]
        return s_row


def PullExtractor():
    return [Features]
