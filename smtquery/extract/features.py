import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
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
            notSolved = len(dataframe.index) - len(dataframe.dropna().index)
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
        #in case some solver could not solve anything; the class names must be extracted so the right ones will be displayed
        sorted_list = Y.sort_values().drop_duplicates().tolist()
        class_names = []
        for i, s in enumerate(self.getSolvers()):
            if i in sorted_list:
                class_names.append(s)

        viz = dtreeviz(dtc, X_train, y_train,
                      target_name="target",
                      feature_names=["numStringVar", "varRatio", "numWEQ", "numQWEQ", "maxNumOfQVar", "scopeIncidence",
                     "largesRatioVarCon", "smallestRatioVarCon", "largestRatioLR", "smallestRatioLR",
                     "numReg", "maxSymb", "maxDepth", "maxNumState", "numLin", "numAsserts",
                     "maxRecDepth", "LenConVars", "WEQVars", "WeqLenVars", "numITE"],
                     
                     class_names=class_names
                       )
        return viz



    def buildTree(self, data):
        # Parameter for Decision Tree
        criterion = 'gini'
        max_d = 10
        max_f = None
        splitter = 'best'
        Y = data.iloc[:, 21]
        data = data.iloc[:, :21]
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

        df = dataframe
        viz = self.buildTree(df.dropna())
        viz.save(os.path.join (path,"decisionTree.svg"))

        report = self.create_report(dataframe, dataframe["path"][0].split(":")[0])
        with open(f"{path}/report.txt", 'w') as f:
            f.write(report)
        f.close()

    def __call__(self, smtfile):
        ast = Probes().getIntel(smtfile)

        Probes().addIntel(smtfile, ast, exprfun.numSymbols(), dict(), "numSymbols")
        Probes().addIntel(smtfile, ast, exprfun.countITE(), dict(), "numITE")
        Probes().addIntel(smtfile, ast, exprfun.maxNesting(), dict(), "maxNesting")
        Probes().addIntel(smtfile, ast, exprfun.WEQProperties(), dict(), "WEQProperties")
        Probes().addIntel(smtfile, ast, exprfun.WeqVars(), dict(), "WeqVars")
        Probes().addIntel(smtfile, ast, exprfun.LenConVars(), dict(), "LenConVars")
        Probes().addIntel(smtfile, ast, exprfun.maxRecDepth(), dict(), "maxRecDepth")
        Probes().addIntel(smtfile, ast, exprfun.WeqLenVars(), dict(), "WeqLenVars")
        Probes().addIntel(smtfile, ast, exprfun.ApproxOfStates(), dict(), "stateApprox")



        intel = ast.intel
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


        if Kind.WEQ in intel["has"]:
            numWEQ = intel["has"][Kind.WEQ]
        if Kind.LENGTH_CONSTRAINT in intel["has"]:
            numLenCon = intel["has"][Kind.LENGTH_CONSTRAINT]
        if Kind.REGEX_CONSTRAINT in intel["has"]:
            numReg = intel["has"][Kind.REGEX_CONSTRAINT]
        if "stateApprox" in intel:
            nfaStates = intel["stateApprox"]

        if "numSymbols" in intel:
            numRegSymbols = len(intel["numSymbols"])

        if "maxNesting" in intel:
            maxNesting = intel["maxNesting"]
        if "numITE" in intel:
            numITE = intel["numITE"]
        if "WEQProperties" in intel:
            prop = intel["WEQProperties"]
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
        if "maxRecDepth" in intel:
            maxRecDepth = intel["maxRecDepth"]
        if "LenConVars" in intel:
            LenConVars = len(max(intel["LenConVars"], key=len, default=set()))
        if "WeqVars" in intel:
            WEQVars = len(max(intel["WeqVars"], key=len, default=set()))
        if "WeqLenVars" in intel:
            WeqLenVars = len(max(intel["WeqLenVars"], key=len, default=set()))
        numAsserts = len(ast)
        name = smtfile.getName()
        solverindex = 0
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

