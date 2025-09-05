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
import itertools
from sklearn.feature_selection import VarianceThreshold
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB
from sklearn.svm import SVC
from sklearn.decomposition import PCA
from sklearn.metrics import classification_report
from imblearn.over_sampling import SMOTE
from sklearn.preprocessing import StandardScaler
import joblib

def add_cross_product_features(df, target_column):
    #extract the features
    feature_cols = []
    for col in df.columns:
        if col == target_column:
            break
        feature_cols.append(col)
    cross_feature_data = {}
    #create cross product of any two
    for col1, col2 in itertools.combinations(feature_cols, 2):
        new_col_name = f"{col1}*{col2}"
        cross_feature_data[new_col_name] = df[col1] * df[col2]
    # Combine cross features into a DataFrame
    cross_features_df = pd.DataFrame(cross_feature_data)

    split_index = df.columns.get_loc(target_column)
    # Concatenate original and new features
    df_combined = pd.concat([df.iloc[:, :split_index], cross_features_df, df.iloc[:, split_index:]], axis=1)
    return df_combined


def feature_reduction(df):
    X = df.drop(columns=["solver"])
    y = df["solver"]
    # remove feature by variance
    vt = VarianceThreshold(threshold=0.0)
    X_var = vt.fit_transform(X)
    # remove feature by correlation
    X_df = pd.DataFrame(X_var)
    corr_matrix = X_df.corr().abs()
    upper = np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
    to_drop = [col for col in range(corr_matrix.shape[1]) if any(corr_matrix[col][upper[:, col]] > 0.95)]
    X_uncorr = X_df.drop(columns=to_drop)

    # splitting by train and test
    X_train, X_test, y_train, y_test = train_test_split(
        X_uncorr, y, stratify=y, test_size=0.2, random_state=42
    )

    # class balancing by SMOTE
    smote = SMOTE(k_neighbors=1, random_state=42)
    X_train_smote, y_train_smote = smote.fit_resample(X_train, y_train)

    #scaling and PCA
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train_smote)
    X_test_scaled = scaler.transform(X_test)

    pca = PCA(n_components=0.95, random_state=42)
    X_train_pca = pca.fit_transform(X_train_scaled)
    X_test_pca = pca.transform(X_test_scaled)

    return X_train_pca, y_train_smote, X_test_pca, y_test


class Features:
    _buildDTC = False
    _solvers = None
    _output_folder = None

    def __init__(self):
        pass

    def getCountOperators(self, p, intels, intel):
        '''
        noString, noRegLan, noStrConcat, noStrLen, noStrSmal, noToRe, noInRe, noReNone, noReAll, \
            noReAllChar, noReConcat, noReUnion, noReInter, noReKleene, noStrOrder, noStrAt, noStrSubstr, \
            noStrPrefix, noStrSuffix, noStrContains, noStrIndex, noStrReplace, noStrReplaceAll, noStrReplaceRe, \
            noSTrReplaceReAll, noReComp, noReDiff, noRePlus, noReOpt, noReRange, noRePower, noReLoop, noStrIsDigit, \
            noStrToCode, noStrFromCode, noStrToInt, noStrFromInt = [0] * 37
        '''

        return_values = [0] * 37
        props = intel[p.getIntelKey2Class(intels[10])]
        variables_to_check = [
            "String", "RegLan", "str.++", "str.len", "str.<", "str.to_re", "str.in_re",
            "re.none", "re.all", "re.allchar", "re.++", "re.union", "re.inter", "re.*",
            "str.<=", "str.at", "str.substr", "str.prefixof", "str.suffixof", "str.contains",
            "str.indexof", "str.replace", "str.replace_all", "str.replace_re", "str.replace_re_all",
            "re.comp", "re.diff", "re.+", "re.opt", "re.range", "re.^", "re.loop",
            "str.is_digit", "str.to_code", "str.from_code", "str.to_int", "str.from_int"
        ]

        for index, name in enumerate(variables_to_check):
            if name in props:
                return_values[index] = props[name]

        return return_values[0], return_values[1], return_values[2], return_values[3], return_values[4], \
            return_values[5], return_values[6], return_values[7], return_values[8], return_values[9], \
            return_values[10], return_values[11], return_values[12], return_values[13], return_values[14], \
            return_values[15], return_values[16], return_values[17], return_values[18], return_values[19], \
            return_values[20], return_values[21], return_values[22], return_values[23], return_values[24], \
            return_values[25], return_values[26], return_values[27], return_values[28], return_values[29], \
            return_values[30], return_values[31], return_values[32], return_values[33], return_values[34], \
            return_values[35], return_values[36]

    def preprocess(self, data):
        solver_col_index = data.columns.get_loc("solver")
        feature_cols = data.columns[:solver_col_index].tolist()

        # 2. Generate hash based on feature values ===
        data["feature_hash"] = data[feature_cols].astype(str).agg("-".join, axis=1)

        # 3. Split data ===
        not_solved = data[data['solver'] == -1].copy()
        solved = data[data['solver'] != -1].copy()

        # 4. Assign dominant solver for each duplicate feature row ===
        dominant_solver = solved.groupby("feature_hash")["solver"].agg(lambda x: x.mode().iloc[0])
        data["solver"] = data["feature_hash"].map(dominant_solver).fillna(data["solver"])

        # 5. Fix invalid solver indexes (solver couldn't solve the instance) ===
        path_index = data.columns.get_loc("path")
        possible_solvers = data.iloc[:, path_index + 1:].values
        current_solvers = data["solver"].astype(int).values

        corrected_solvers = []
        for i, solver_idx in enumerate(current_solvers):
            if solver_idx == -1:
                corrected_solvers.append(solver_idx)
            elif solver_idx >= len(possible_solvers[i]) or possible_solvers[i][solver_idx] == 0:
                if 1 in possible_solvers[i]:
                    corrected_solvers.append(possible_solvers[i].tolist().index(1))
                else:
                    corrected_solvers.append(solver_idx)  # no valid replacement
            else:
                corrected_solvers.append(solver_idx)

        data["solver"] = corrected_solvers

        # === 6. Handle remaining -1 (unsolved) ===
        if (data["solver"] == -1).any():
            most_common_solver = data[data["solver"] != -1]["solver"].value_counts().idxmax()
            data.loc[data["solver"] == -1, "solver"] = most_common_solver

        # === 7. Drop helper column and return ===
        data.drop(columns=["feature_hash"], inplace=True)
        return data.reset_index(drop=True)

    def create_report(self, dataframe, benchmarkName):
        report = "Report for Benchmark: " + benchmarkName + " with " + str(len(dataframe.index)) + " instances \n"
        report = report + "\n"

        columns = dataframe.columns
        for column in columns[:-2]:
            report = report + column + " "
            avgc = dataframe[column].mean()
            report = report + f"Average: {avgc}"
            for i, s in enumerate(self.getSolvers()):
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
        # in case some solver could not solve anything; the class names must be extracted so the right ones will be displayed
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

    def getSolvers(self):
        if self._solvers == None:
            self._solvers = list(smtquery.config.getConfiguration().getSolvers().keys())
        return self._solvers

    def getOutputFolder(self):
        if self._output_folder == None:
            if self._buildDTC:
                self._output_folder = os.path.join(smtquery.config.getConfiguration().getOutputLocation(),
                                                   "DecisionTree")
            else:
                self._output_folder = os.path.join(smtquery.config.getConfiguration().getOutputLocation(), "Features")
        return self._output_folder

    def finalise(self, results, total):
        '''columns = ["numStringVar", "varRatio", "numWEQ", "numQWEQ", "maxNumOfQVar", "scopeIncidence",
                   "largestRatioVarCon", "smallestRatioVarCon", "largestRatioLR", "smallestRatioLR",
                   "numReg", "maxSymb", "maxDepth", "maxNumState", "numLin", "numAsserts",
                   "maxRecDepth", "LenConVars", "WEQVars", "WeqLenVars", "numITE", "solver", "path"]'''
        columns = ["numStringVar", "varRatio", "numWEQ", "numQWEQ", "maxNumOfQVar", "scopeIncidence",
                   "largestRatioVarCon", "smallestRatioVarCon", "largestRatioLR", "smallestRatioLR",
                   "numReg", "maxSymb", "maxDepth", "maxNumState", "numLin", "numAsserts",
                   "maxRecDepth", "LenConVars", "WEQVars", "WeqLenVars", "numITE", "noString", "noRegLan",
                   "noStrConcat",
                   "noStrLen", "noStrSmal", "noToRe", "noInRe", "noReNone", "noReAll",
                   "noReAllChar", "noReConcat", "noReUnion", "noReInter", "noReKleene", "noStrOrder", "noStrAt",
                   "noStrSubstr",
                   "noStrPrefix", "noStrSuffix", "noStrContains", "noStrIndex", "noStrReplace", "noStrReplaceAll",
                   "noStrReplaceRe",
                   "noSTrReplaceReAll", "noReComp", "noReDiff", "noRePlus", "noReOpt", "noReRange", "noRePower",
                   "noReLoop", "noStrIsDigit",
                   "noStrToCode", "noStrFromCode", "noStrToInt", "noStrFromInt", "solver", "path"]

        for i, s in enumerate(self.getSolvers()):
            columns.append(s)

        results1 = []
        for row in results:
            if row == None:
                continue
            if len(row) == len(columns):
                results1.append(row)
            else:
                print(row)
        dataframe = pd.DataFrame(columns=columns, data=results1)

        path = os.path.join(self.getOutputFolder(), str(int(time.time())))
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

            df = add_cross_product_features(dataframe, target_column='solver')
            df_preprocessed = self.preprocess(df)

            # Keep only feature and solver
            solver_col_index = df_preprocessed.columns.get_loc("solver")
            feature_cols = df_preprocessed.columns[:solver_col_index].tolist()
            final_data = df_preprocessed[feature_cols + ["solver"]]

            try:
                X_train, Y_train, X_test, Y_test = feature_reduction(final_data)
            except ValueError as e:
                if "least populated class" in str(e):
                    print("Skipping RandomForest: not enough samples per class.")
                else:
                    raise
            else:
                # hyperparameters for RandomForest classifier
                rf_best = RandomForestClassifier(
                    n_estimators=300,
                    max_depth=50,
                    min_samples_split=2,
                    min_samples_leaf=1,
                    random_state=42,
                    n_jobs=-1
                )
                model = rf_best.fit(X_train, Y_train)
                y_pred = model.predict(X_test)
                joblib.dump(model, os.path.join(path, "random_forest_model.pkl"))


        else:
            # build decision tree
            viz = self.buildTree(dataframe)
            viz.save(os.path.join(path, "decisionTree.svg"))

    def __call__(self, smtfile):

        intels = [smtquery.smtcon.exprfun.numSymbols,  # 0
                  smtquery.smtcon.exprfun.countITE,  # 1
                  smtquery.smtcon.exprfun.maxNesting,  # 2
                  smtquery.smtcon.exprfun.WEQProperties,  # 3
                  smtquery.smtcon.exprfun.WeqVars,  # 4
                  smtquery.smtcon.exprfun.LenConVars,  # 5
                  smtquery.smtcon.exprfun.maxRecDepth,  # 6
                  smtquery.smtcon.exprfun.WeqVars,  # 7
                  smtquery.smtcon.exprfun.ApproxOfStates,  # 8
                  smtquery.smtcon.exprfun.HasAtom,  # 9
                  smtquery.smtcon.exprfun.CountOperators]  # 10

        p = Probes()
        ast = p.getIntel(smtfile, intels)
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
        varRatio = numStringVars / allVars
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
        if p.getIntelKey2Class(intels[10]) in intel:
            noString, noRegLan, noStrConcat, noStrLen, noStrSmal, noToRe, noInRe, noReNone, noReAll, \
                noReAllChar, noReConcat, noReUnion, noReInter, noReKleene, noStrOrder, noStrAt, noStrSubstr, \
                noStrPrefix, noStrSuffix, noStrContains, noStrIndex, noStrReplace, noStrReplaceAll, noStrReplaceRe, \
                noSTrReplaceReAll, noReComp, noReDiff, noRePlus, noReOpt, noReRange, noRePower, noReLoop, noStrIsDigit, \
                noStrToCode, noStrFromCode, noStrToInt, noStrFromInt = self.getCountOperators(p, intels, intel)

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

        '''s_row = [numStringVars, varRatio, numWEQ, numQWEQ, maxNumQVar, scopeCoincidence, largestRatioVarCon,
                 smallestRatioVarCon, largestRatioLR, smallestRatioLR, numReg, numRegSymbols, maxNesting, nfaStates,
                 numLenCon,
                 numAsserts, maxRecDepth, LenConVars, WEQVars, WeqLenVars, numITE, solverindex, name]'''

        s_row = [numStringVars, varRatio, numWEQ, numQWEQ, maxNumQVar, scopeCoincidence, largestRatioVarCon,
                 smallestRatioVarCon, largestRatioLR, smallestRatioLR, numReg, numRegSymbols, maxNesting, nfaStates,
                 numLenCon,
                 numAsserts, maxRecDepth, LenConVars, WEQVars, WeqLenVars, numITE, noString, noRegLan, noStrConcat,
                 noStrLen, noStrSmal, noToRe, noInRe, noReNone, noReAll,
                 noReAllChar, noReConcat, noReUnion, noReInter, noReKleene, noStrOrder, noStrAt, noStrSubstr,
                 noStrPrefix, noStrSuffix, noStrContains, noStrIndex, noStrReplace, noStrReplaceAll, noStrReplaceRe,
                 noSTrReplaceReAll, noReComp, noReDiff, noRePlus, noReOpt, noReRange, noRePower, noReLoop, noStrIsDigit,
                 noStrToCode, noStrFromCode, noStrToInt, noStrFromInt, solverindex, name]

        for i in solverCheck:
            s_row.append(i)
        return s_row


class FeatureEx(Features):
    _buildDTC = False

    @staticmethod
    def getName():
        return "Features"


class DecisionTree(Features):
    _buildDTC = True

    @staticmethod
    def getName():
        return "DecisionTree"


def PullExtractor():
    return [FeatureEx, DecisionTree]


