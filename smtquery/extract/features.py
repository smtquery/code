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
import numpy as np
import time


class Features:
    _buildDTC = False
    _solvers = None
    _output_folder = None

    def __init__(self):
        pass

    def preprocess(self, data):
        columns_to_check = ['numStringVar', 'varRatio', 'numWEQ', 'numQWEQ', 'maxNumOfQVar', 'scopeIncidence',
                            'largestRatioVarCon', 'smallestRatioVarCon', 'largestRatioLR', 'smallestRatioLR', 'numReg',
                            'maxSymb', 'maxDepth', 'maxNumState', 'numLin', 'numAsserts', 'maxRecDepth', 'LenConVars',
                            'WEQVars', 'WeqLenVars', 'numITE']
        #split into solvable and not solvable instances
        notSolved = data[data['solver'] == -1]
        solved = data[data['solver'] != -1]

        # get duplicates and change class
        duplicates = solved.duplicated(subset=columns_to_check, keep=False)
        dominant_classes = solved.groupby(columns_to_check)['solver'].apply(lambda x: x.mode().iloc[0])
        solved.loc[duplicates, 'solver'] = solved[duplicates].set_index(columns_to_check).index.map(
            dominant_classes).values
        # change class back if it could not solve anything
        bestSolver = solved.loc[:, ['solver']].values.tolist()
        path_index = solved.columns.get_loc("path")
        possibleSolver = solved.iloc[:, path_index + 1:].values.tolist()

        solver_list = []
        for i in range(len(bestSolver)):
            solverindex = bestSolver[i][0]
            if possibleSolver[i][solverindex] == 0:
                if 1 in possibleSolver[i]:
                    ind = possibleSolver[i].index(1)
                    solver_list.append(ind)
            else:
                solver_list.append(bestSolver[i][0])

        solver_df = pd.DataFrame({'solver': solver_list}, dtype=int)
        solved.update(solver_df)



        if not notSolved.empty:
            #if an unsolvable instance (tuple), was solved somewhere: set it to that class
            solver_index = data.columns.get_loc('solver')
            tmp = data.iloc[:, :solver_index].values.tolist()
            notSolved_list = notSolved.iloc[:, :].values.tolist()

            for i, item in enumerate(notSolved_list):
                if item[:solver_index] in tmp:
                    index_in_tmp = tmp.index(item[:solver_index])  # Index in tmp, where it occurs
                    notSolved.iloc[i, notSolved.columns.get_loc('solver')] = data.iloc[
                        index_in_tmp, data.columns.get_loc('solver')]

            #split the new dataset again, into solvable and not solvable
            notyetSolved = notSolved[notSolved['solver'] == -1]
            solvedNew = notSolved[notSolved['solver'] != -1]

            solvedNew = solvedNew.reset_index(drop=True)
            solved = pd.concat([solved, solvedNew], axis=0).reset_index(drop=True)

            #set unsolvable instances to the most dominant class
            most_succesful_class = solved["solver"].value_counts().idxmax()
            mscDF = pd.DataFrame([most_succesful_class] * len(notSolved.index), dtype=int)
            notyetSolved= notyetSolved.reset_index(drop=True)
            notyetSolved['solver'] = mscDF
            solved = pd.concat([solved, notyetSolved], axis=0).reset_index(drop=True)
            return solved
        else:
            return solved

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
        y = np.array(y, dtype=int)
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
        data1 = self.preprocess(data)
        solver_index = data1.columns.get_loc("solver")
        columns_to_drop = data1.columns[solver_index:]
        # Parameter for Decision Tree
        X = data1.drop(columns=columns_to_drop)

        y = data1['solver']

        # Parameter for Decision Tree
        criterion = 'gini'
        max_d = 15
        max_f = None
        splitter = 'best'
        dtc = DecisionTreeClassifier()
        return self.trainAndTestDTC(dtc, X, y, criterion, max_d, max_f, splitter)

    @staticmethod
    def getName():
        return "FeaturesAux"

    def getSolvers (self):
        if self._solvers == None:
            self._solvers = list(smtquery.config.getConfiguration().getSolvers().keys ())
        return self._solvers

    def getOutputFolder (self):
        if self._output_folder == None:
            if self._buildDTC:
                self._output_folder = os.path.join(smtquery.config.getConfiguration ().getOutputLocation (),"DecisionTree")
            else:
                self._output_folder = os.path.join(smtquery.config.getConfiguration ().getOutputLocation (),"Features")
        return self._output_folder
    
    def finalise(self, results, total):        
        columns=["numStringVar", "varRatio", "numWEQ", "numQWEQ", "maxNumOfQVar", "scopeIncidence",
                     "largestRatioVarCon", "smallestRatioVarCon", "largestRatioLR", "smallestRatioLR",
                     "numReg", "maxSymb", "maxDepth", "maxNumState", "numLin", "numAsserts",
                     "maxRecDepth", "LenConVars", "WEQVars", "WeqLenVars", "numITE", "solver", "path"]

        for i, s in enumerate(self.getSolvers()):
            columns.append(s)

        dataframe = pd.DataFrame(columns=columns, data=results)
        path = os.path.join (self.getOutputFolder(),str(int(time.time())))
        os.makedirs(path, exist_ok=True)


        if not self._buildDTC:
            # export features.csv
            dataframe.to_csv(os.path.join(path, "features.csv"), index=False)

            # gen report
            path_index = dataframe.columns.get_loc("path")
            reportDF = dataframe.iloc[:, :path_index + 1]
            report = self.create_report(reportDF, reportDF["path"][0].split(":")[0])
            with open(f"{path}/report.txt", 'w') as f:
                f.write(report)

        else: 
            # build decision tree
            viz = self.buildTree(dataframe)
            viz.save(os.path.join (path,"decisionTree.svg"))   

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
        solvertime = smtquery.config.getConfiguration().getRunParameters()["timeout"]
        _storage = smtquery.config.getConfiguration().getStorage()
        res = _storage.getResultsForInstance(smtfile)
        solverCheck = []
        for i, s in enumerate(self.getSolvers()):
            solverCheck.append(i)
        for i, s in enumerate(self.getSolvers()):
            if res[s]["result"] in [Result.NotSatisfied, Result.Satisfied]:
                if res[s]["time"] < solvertime:
                    solvertime = res[s]["time"]
                    solverindex = i
                solverCheck[i] = 1
            else:
                solverCheck[i] = 0


        s_row = [numStringVars, varRatio, numWEQ, numQWEQ, maxNumQVar, scopeCoincidence, largestRatioVarCon,
                 smallestRatioVarCon, largestRatioLR, smallestRatioLR, numReg, numRegSymbols, maxNesting, nfaStates, numLenCon,
                 numAsserts, maxRecDepth, LenConVars, WEQVars, WeqLenVars, numITE, solverindex, name]
        for i in solverCheck:
            s_row.append(i)
        return s_row


class FeatureEx(Features):
    _buildDTC = False
    @staticmethod
    def getName ():
        return "Features"
    
class DecisionTree(Features):
    _buildDTC = True
    @staticmethod
    def getName ():
        return "DecisionTree"

def PullExtractor():
    return [FeatureEx,DecisionTree]

