
def getScopeIncidence(scopes, isVar):
    res = [0 for i in isVar]
    for scope in scopes:
        for j in range(scope[0], scope[1]):
            res[j] += 1
    if len(isVar) < 1:
        return 0
    return max(res)

def getNumQWEQ(equations):
    numQWEQ = 0
    maxNumOfQVar = 0
    maxIncidence = 0
    for eq in equations:
        scopesL = []
        scopesR = []
        maxNumOfQVarTMP = 0
        isQWEQ = False
        for i in range(len(eq.isVarLHS)):
            if eq.isVarLHS[i] == 1:
                if i == 0:
                    var = eq.LHS[0 : eq.endPointsLHS[i] + 1]
                else:
                    var = eq.LHS[eq.endPointsLHS[i-1] + 1 : eq.endPointsLHS[i] + 1]

                for j in range(i+1, len(eq.isVarLHS)):
                    if eq.isVarLHS[j] == 1 and (var == eq.LHS[eq.endPointsLHS[j-1] + 1 : eq.endPointsLHS[j] + 1]):
                        isQWEQ = True
                        maxNumOfQVarTMP += 1
                        scopesL.append((i,j))

        for i in range(len(eq.isVarRHS)):
            if eq.isVarRHS[i] == 1:
                if i == 0:
                    var = eq.LHS[0 : eq.endPointsRHS[i] + 1]
                else:
                    var = eq.LHS[eq.endPointsRHS[i-1] + 1 : eq.endPointsRHS[i] + 1]

                for j in range(i+1, len(eq.isVarRHS)):
                    if eq.isVarRHS[j] == 1 and (var == eq.RHS[eq.endPointsRHS[j-1] + 1 : eq.endPointsRHS[j] + 1]):
                        isQWEQ = True
                        maxNumOfQVarTMP += 1
                        scopesR.append((i, j))

        incidenceL = getScopeIncidence(scopesL, eq.isVarLHS)
        incidenceR = getScopeIncidence(scopesR, eq.isVarRHS)
        if incidenceL > incidenceR:
            tmpIn = incidenceL
        elif incidenceR >= incidenceL:
            tmpIn = incidenceR

        if tmpIn >= maxIncidence:
            maxIncidence = tmpIn

        if isQWEQ:
            numQWEQ += 1
        if maxNumOfQVarTMP > maxNumOfQVar:
            maxNumOfQVar = maxNumOfQVarTMP

    return numQWEQ, maxNumOfQVar, maxIncidence


def getRatioVarCon(equations):
    smallestVarCon = 10000
    largestVarCon = 0
    for eq in equations:
        numVars = 0
        numCon = 0
        for i in range(len(eq.isVarLHS)):
            if eq.isVarLHS[i] == 1:
                numVars += 1
            else:
                if i == 0:
                    tmp = eq.endPointsLHS[i]
                else:
                    tmp = (eq.endPointsLHS[i] + 1) - (eq.endPointsLHS[i-1] + 1)
                numCon += tmp
        for i in range(len(eq.isVarRHS)):
            if eq.isVarRHS[i] == 1:
                numVars += 1
            else:
                if i == 0:
                    tmp = eq.endPointsRHS[i]
                else:
                    tmp = (eq.endPointsRHS[i] + 1) - (eq.endPointsRHS[i-1] + 1)
                numCon += tmp
        if numVars > 0 and numCon > 0:
            ratio = numVars / numCon
        elif numVars > 0 and numCon == 0:
            ratio = numVars
        elif numVars == 0 and numCon > 0:
            ratio = numCon
        else:
            ratio = 0
        if ratio >= largestVarCon:
            largestVarCon = ratio
        if ratio <=  smallestVarCon:
            smallestVarCon = ratio

    return largestVarCon, smallestVarCon


def getRatioLR(equations):
    smallestLR = 10000
    largestLR = 0

    for eq in equations:
        lengthL = 0
        lengthR = 0
        for i in range(len(eq.isVarLHS)):
            if eq.isVarLHS[i] == 1:
                lengthL += 1
            else:
                if i == 0:
                    tmp = eq.endPointsLHS[i]
                else:
                    tmp =  (eq.endPointsLHS[i] + 1) - (eq.endPointsLHS[i-1] + 1)
                lengthL += tmp
        for i in range(len(eq.isVarRHS)):
            if eq.isVarRHS[i] == 1:
                lengthR += 1
            else:
                if i == 0:
                    tmp = eq.endPointsRHS[i]
                else:
                    tmp = (eq.endPointsRHS[i] + 1) - (eq.endPointsRHS[i-1] + 1)
                lengthR += tmp
        if lengthL > 0 and lengthR > 0:
            ratio = lengthL / lengthR
        elif lengthL > 0 and lengthR == 0:
            ratio = lengthL
        elif lengthL == 0 and lengthR > 0:
            ratio = lengthR
        else:
            ratio = 0
        if ratio >= largestLR:
            largestLR = ratio
        if ratio <=  smallestLR:
            smallestLR = ratio

    return largestLR, smallestLR

def extractFeatures(equations, variables):
    numQWEQ, maxNumOfQVar, scopeIncidence = getNumQWEQ(equations)
    largesRatioVarCon, smallestRatioVarCon = getRatioVarCon(equations)
    largestRatioLR, smallestRatioLR = getRatioLR(equations)
    return numQWEQ, maxNumOfQVar, scopeIncidence, largesRatioVarCon, smallestRatioVarCon, largestRatioLR, smallestRatioLR

