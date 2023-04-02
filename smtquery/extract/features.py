import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier

import smtquery.ui
from smtquery.solvers.solver import *

from smtquery.intel.plugins.probes import Probes

from smtquery.extract.featureExtractionFiles import newParse

from smtquery.extract.featureExtractionFiles import extractFeatWE

from smtquery.extract.featureExtractionFiles import regexParser
import graphviz
from sklearn import tree
from dtreeviz.trees import dtreeviz





class Features:
    output_folder = "./output/Features/"

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
            report = report + "Average: " + str(avgc) +" Average for Z3Str3: " + str(avgStr) + " Average for Z3Seq: " + str(avgSeq) + " Average for CVC5: " + str(avgCvc) + "\n"
        notSolved = len(dataframe.index) - len(dataframe.dropna().index)
        report = report + "\n"
        report = report + "Number of not solvable instances: " + str(notSolved) + "\n"
        report = report + "Instances solved by Z3Str3: " + str(len(dataframe[dataframe['solver'] == 1])) + "\n"
        report = report + "Instances solved by Z3Seq: " + str(len(dataframe[dataframe['solver'] == 0])) + "\n"
        report = report + "Instances solved by CVC5: " + str(len(dataframe[dataframe['solver'] == 2])) + "\n"
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
                      class_names=['Z3Seq', 'Z3Str3','CVC5'])
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

        dataframe = pd.DataFrame(
            columns=["numStringVar", "varRatio", "numWEQ", "numQWEQ", "maxNumOfQVar", "scopeIncidence",
                     "largesRatioVarCon", "smallestRatioVarCon", "largestRatioLR", "smallestRatioLR",
                     "numReg", "maxSymb", "maxDepth", "maxNumState", "numLin", "numAsserts",
                     "maxRecDepth", "solver", "path"], data=results)

        path = self.output_folder + dataframe["path"][0].split(":")[0]
        os.makedirs(path, exist_ok=True)
        _ = dataframe.to_csv(f"{path}/features.csv", index=False)

        df = dataframe
        viz = self.buildTree(df.dropna())
        viz.save(f"{path}/decisionTree.svg")

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

        maxDepth = max(RGXdepths)
        maxSymb = max(alphabets)
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
        if res["Z3Seq"]["result"] in [Result.NotSatisfied, Result.Satisfied]:
            a = res["Z3Seq"]["time"]
        else:
            a = 1000
        if res["Z3Str3"]["result"] in [Result.NotSatisfied, Result.Satisfied]:
            b = res["Z3Str3"]["time"]
        else:
            b = 1000
        if res["CVC5"]["result"] in [Result.NotSatisfied, Result.Satisfied]:
            c = res["CVC5"]["time"]
        else:
            c = 1000
        r = [a, b, c]
        solver = r.index(min(r))
        if solver == 1000:
            solver = "NaN"
        name = smtfile.getName()
        s_row = [numStringVar, varRatio, numWEQ, numQWEQ, maxNumOfQVar, scopeIncidence, largesRatioVarCon,
                 smallestRatioVarCon, largestRatioLR, smallestRatioLR, numReg, maxSymb, maxDepth, maxNumState, numLin,
                 numasserts, recDepth, solver, name]
        return s_row


def PullExtractor():
    return [Features]
