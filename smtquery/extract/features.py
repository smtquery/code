import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
import smtquery.smtcon
import smtquery.smtcon.exprfun
import smtquery.ui
from smtquery.intel.plugins import probes
from smtquery.intel.plugins.probes import Probes
from smtquery.smtcon import exprfun
from smtquery.smtcon.expr import Sort, Kind
from smtquery.solvers.solver import *
from automata.fa.dfa import DFA
from smtquery.extract.featureExtractionFiles import newParse
from smtquery.extract.featureExtractionFiles import extractFeatWE
import graphviz
from sklearn import tree
from dtreeviz.trees import dtreeviz
import smtquery.config

class Features:
    def __init__(self):
        self._solvers = None
        self._output_folder = None
        
    def create_report(self, dataframe, benchmarkName):
        report = "Report for Benchmark: " + benchmarkName + " with " + str(len(dataframe.index)) + " instances \n"
        report = report + "\n"

        columns = dataframe.columns
        for column in columns[:-2]:
            report = report + column + " "
            avgc = dataframe[column].mean()
            report = report + f"Average: {avgc}"
            for i,s in enumerate(self.getSolvers ()):
                mean = dataframe.loc[dataframe['solver'] == i, column].mean()
                
                report += f" Average for {s}: {mean}"
            report += "\n"
        notSolved = len(dataframe.index) - len(dataframe[dataframe['solver'] != -1].index)
        report += f"Number of Not solved instances: {notSolved}"
        report += "\n"
        return report



    def trainAndTestDTC(self, dtc, data, Y, crit, depth, feat, split):
        y = Y.values.ravel()
        X = data
        dtc.feature_names = X.columns
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1, random_state=42)
        dtc.criterion = crit
        dtc.max_depth = depth
        dtc.max_features = feat
        dtc.splitter = split

        dtc.fit(X_train.values, y_train)
        #in case some solver could not solve anything; the class names must be extracted so the right ones will be displayed
        sorted_list = Y.sort_values().drop_duplicates().tolist()
        class_names = []
        for i, s in enumerate(self.getSolvers()):
            if i in sorted_list:
                class_names.append(s)

        viz = dtreeviz(dtc, X_train, y_train,
                    target_name="target",
                    feature_names=dtc.feature_names,
                    class_names=class_names
                    )
        return viz

    def buildTree(self, data):
        # Parameter for Decision Tree
        criterion = 'gini'
        max_d = 10
        max_f = None
        splitter = 'best'

        Y = data["solver"]
        data = data.drop(['solver', 'path'], axis=1)
        dtc = DecisionTreeClassifier()
        return self.trainAndTestDTC(dtc, data, Y, criterion, max_d, max_f, splitter)

    @staticmethod
    def getName():
        return "Features"

    def getSolvers (self):
        if self._solvers == None:
            self._solvers = list(smtquery.config.getConfiguration().getSolvers().keys ())
        return self._solvers

    def getOutputFolder (self):
        if self._output_folder == None:
            self._output_folder = os.path.join(smtquery.config.getConfiguration ().getOutputLocation (),"Features")
        return self._output_folder
    
    def finalise(self, results, total):        
        dataframe = pd.DataFrame(
            columns=["numStringVar", "varRatio", "numWEQ", "numQWEQ", "maxNumOfQVar", "scopeIncidence",
                     "largestRatioVarCon", "smallestRatioVarCon", "largestRatioLR", "smallestRatioLR",
                     "numReg", "maxSymb", "maxDepth", "maxNumState", "numLin", "numAsserts",
                     "maxRecDepth", "LenConVars", "WEQVars", "WeqLenVars", "numITE", "solver", "path"], data=results)

        path = os.path.join (self.getOutputFolder (),dataframe["path"][0].split(":")[0])
        os.makedirs(path, exist_ok=True)
        dataframe.to_csv(os.path.join (path,"features.csv"), index=False)
        report = self.create_report(dataframe, dataframe["path"][0].split(":")[0])
        viz = self.buildTree(dataframe[dataframe['solver'] != -1])
        viz.save(os.path.join (path,"decisionTree.svg"))

        
        with open(f"{path}/report.txt", 'w') as f:
            f.write(report)
        f.close()

    def __call__(self, smtfile):
        intels = [smtquery.smtcon.exprfun.numSymbols,      #0
                  smtquery.smtcon.exprfun.countITE,        #1
                  smtquery.smtcon.exprfun.maxNesting,      #2
                  smtquery.smtcon.exprfun.WEQProperties,   #3
                  smtquery.smtcon.exprfun.WeqVars,         #4
                  smtquery.smtcon.exprfun.LenConVars,      #5
                  smtquery.smtcon.exprfun.maxRecDepth,     #6
                  smtquery.smtcon.exprfun.WeqVars,         #7
                  smtquery.smtcon.exprfun.ApproxOfStates,  #8
                  smtquery.smtcon.exprfun.HasAtom]         #9
        p = Probes()
        ast = p.getIntel(smtfile,intels)
        intel = ast.get_intel()

        numStringVars = 0
        vars = intel["variables"]
        allVars = 1
        if Sort.String in vars:
            numStringVars = len(vars[Sort.String])
            allVars = len(vars[Sort.String])
        if Sort.Bool in vars:

            allVars += len(vars[Sort.Bool])
        if Sort.Int in vars:
            allVars += len(vars[Sort.Int])
        varRatio = numStringVars/allVars
        numWEQ = 0
        numLenCon = 0
        numReg = 0
        nfaStates = 0
        numRegSymbols = 0
        maxNesting = 0
        numITE = 0
        numQWEQ = 0
        maxNumQVar = 0
        scopeCoincidence = 0
        largestRatioLR = 0
        smallestRatioLR = 0
        largestRatioVarCon = 0
        smallestRatioVarCon = 0
        WEQVars = 0
        LenConVars = 0
        WeqLenVars = 0
        maxRecDepth = 0


        if Kind.WEQ in intel[p.getIntelKey2Class(intels[9])]:
            numWEQ = intel[p.getIntelKey2Class(intels[9])][Kind.WEQ]
        if Kind.LENGTH_CONSTRAINT in intel[p.getIntelKey2Class(intels[9])]:
            numLenCon = intel[p.getIntelKey2Class(intels[9])][Kind.LENGTH_CONSTRAINT]
        if Kind.REGEX_CONSTRAINT in intel[p.getIntelKey2Class(intels[9])]:
            numReg = intel[p.getIntelKey2Class(intels[9])][Kind.REGEX_CONSTRAINT]
        if p.getIntelKey2Class(intels[8]) in intel:
            nfaStates = intel[p.getIntelKey2Class(intels[8])]

        if p.getIntelKey2Class(intels[0]) in intel:
            numRegSymbols = len(intel[p.getIntelKey2Class(intels[0])])

        if p.getIntelKey2Class(intels[2]) in intel:
            maxNesting = intel[p.getIntelKey2Class(intels[2])]
        if p.getIntelKey2Class(intels[1]) in intel:
            numITE = intel[p.getIntelKey2Class(intels[1])]
        if p.getIntelKey2Class(intels[3]) in intel:
            prop = intel[p.getIntelKey2Class(intels[3])]
            numQWEQ = prop["numQWEQ"]
            maxNumQVar = prop["maxNumOfQVar"]
            scopeCoincidence = prop["scopeCoincidence"]
            largestRatioLR = prop["largestRatioLR"]
            smallestRatioLR = prop["smallestRatioLR"]
            largestRatioVarCon = prop["largestRatioVarCon"]
            smallestRatioVarCon = prop["smallestRatioVarCon"]
            if str(smallestRatioLR) == "inf":
                smallestRatioLR = 0
            if str(smallestRatioVarCon) == "inf":
                smallestRatioVarCon = 0
        if p.getIntelKey2Class(intels[6]) in intel:
            maxRecDepth = intel[p.getIntelKey2Class(intels[6])]
        if p.getIntelKey2Class(intels[5]) in intel:
            LenConVars = len(max(intel[p.getIntelKey2Class(intels[5])], key=len, default=set()))
        if p.getIntelKey2Class(intels[4]) in intel:
            WEQVars = len(max(intel[p.getIntelKey2Class(intels[4])], key=len, default=set()))
        if p.getIntelKey2Class(intels[5]) in intel:
            WeqLenVars = len(max(intel[p.getIntelKey2Class(intels[5])], key=len, default=set()))
        numAsserts = len(ast)
        name = smtfile.getName()
        solverindex = -1
        solvertime = 1000
        _storage = smtquery.config.getConfiguration().getStorage()
        res = _storage.getResultsForInstance(smtfile)
        for i, s in enumerate(self.getSolvers()):
            if res[s]["result"] in [Result.NotSatisfied, Result.Satisfied]:
                if res[s]["time"] < solvertime:
                    solvertime = res[s]["time"]
                    solverindex = i


        s_row = [numStringVars, varRatio, numWEQ, numQWEQ, maxNumQVar, scopeCoincidence, largestRatioVarCon,
                 smallestRatioVarCon, largestRatioLR, smallestRatioLR, numReg, numRegSymbols, maxNesting, nfaStates, numLenCon,
                 numAsserts, maxRecDepth, LenConVars, WEQVars, WeqLenVars, numITE, solverindex, name]

        return s_row



def PullExtractor():
    return [Features]

