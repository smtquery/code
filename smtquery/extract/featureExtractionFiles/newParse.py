from z3 import z3

from smtquery.extract.featureExtractionFiles.generalClasses import Equation
from smtquery.smtcon.exprfun import *
from smtquery.smtcon.expr import Kind


def extractWEQ(side, res):
    if side.is_const():
        s = str(side)
        i = 0
        while s[i] == " ":
            i += 1
        i = i +1
        j = len(s)-1
        while s[j] == " ":
            j -= 1
        s = s[i:j]
        if s == '':
            return res
        res.append((s, len(s), 0))
        return res
    elif side.is_variable():
        s = str(side)
        i = 0
        while s[i] == " " or s[i] == "\"":
            i += 1
        j = len(s) - 1
        while s[j] == " " or s[j] == "\"":
            j -= 1
        s = s[i:j + 1]
        res.append((s, len(s), 1))
        return res
    elif len(side.children()) > 0:
        for node in side.children():
            extractWEQ(node, res)
        return res


def exRE(param, rgx):
    rgx = ""
    k = param.decl()
    if k == "re.allchar":
        return "a-zA-Z"
    elif k == "re.range":
        l = str(param.children()[0])
        i = 0
        while l[i] == " ":
            i += 1
        i = i + 1
        j = len(l) - 1
        while l[j] == " ":
            j -= 1
        l = l[i:j]
        r = str(param.children()[1])
        i = 0
        while r[i] == " ":
            i += 1
        i = i + 1
        j = len(r) - 1
        while r[j] == " ":
            j -= 1
        r = r[i:j]
        rgx = l + "-" + r
    elif k == "str.to_re":
        rgx += exRE(param.children()[0], rgx)
    elif k == "str.to.re":
        rgx += exRE(param.children()[0], rgx)
    elif k == "re.++":
        rgx += exRE(param.children()[0], rgx) + "" + exRE(param.children()[1], rgx)
    elif k =='re.*':
        rgx = "(" + exRE(param.children()[0], rgx) + ")*"
    elif k == 're.+':
        rgx += "(" + exRE(param.children()[0], rgx) + ")+"
    elif k =='re.union':
        rgx += "(" + exRE(param.children()[0], rgx) + ")(" + exRE(param.children()[1], rgx) + ")|"
    elif k == "str.in_re":
        m  = param.children()[1]
        rgx = exRE(m, rgx)
    elif param.is_const():
        s = str(param)

        s = s.replace("|", "k")
        s = s.replace("*", "l")
        s = s.replace("+", "m")
        s = s.replace("(", "n")
        s = s.replace(")", "o")
        s = s.replace("\"", "p")
        s = s.replace("'", "q")
        s = s.replace("{", "r")
        s = s.replace("}", "s")
        s = s.replace(".", "t")
        s = s.replace("´", "u")
        s = s.replace("`", "v")
        s = s.replace("\'", "x")
        s = s.replace('"', "y")
        s = s.replace('[', "z")
        s = s.replace(']', "a")
        i = 0
        while s[i] == " ":
            i += 1
        i = i + 1
        j = len(s) - 1
        while s[j] == " ":
            j -= 1
        rgx = s[i:j]
        if len(rgx) == 0:
            rgx = 'w'
        return rgx
    elif param.is_variable():
        return rgx

    return rgx



def recursivelyFindRegexOrWEQ(param, WEQ, RGX, numLenCon):
    for i in range(len(param)):
        if param[i].kind() == Kind.WEQ:
            children = param[i].children()
            lhs = children[0]
            rhs = children[1]
            left = []
            left = extractWEQ(lhs, left)
            right = []
            right = extractWEQ(rhs, right)
            if len(left) < 1:
                left = [('', 0, 0)]
            if len(right) < 1:
                right = [('', 1, 0)]
            lhs = left[0][0]  # erster eintrag der linken seite
            lhsRange = [left[0][1] - 1]  # startet bei 0 deswegen - 1
            lhsVars = [left[0][2]]  # gibt an ob es eine variable ist oder nicht

            rhs = right[0][0]  # erster eintrag der rechten seite
            rhsRange = [right[0][1] - 1]  # startet bei 0 deswegen - 1
            rhsVars = [right[0][2]]  # gibt an ob es eine variable ist oder nicht

            for i in range(1, len(left)):
                lhs += left[i][0]
                lhsRange.append(lhsRange[i - 1] + left[i][1])
                lhsVars.append(left[i][2])
            for i in range(1, len(right)):
                rhs += right[i][0]
                rhsRange.append(rhsRange[i - 1] + right[i][1])
                rhsVars.append(right[i][2])

            eq = Equation()
            eq.LHS = lhs
            eq.RHS = rhs
            eq.endPointsLHS = lhsRange
            eq.endPointsRHS = rhsRange
            eq.isVarLHS = lhsVars
            eq.isVarRHS = rhsVars
            eq.displayText = lhs + " = " + rhs
            WEQ.append(eq)
            #return
        elif param[i].kind() == Kind.REGEX_CONSTRAINT:
            rgx = ""

            rgx = exRE(param[i], rgx)
            RGX.append(rgx)
            #return
        elif param[i].kind() == Kind.LENGTH_CONSTRAINT:

            numLenCon[0] += 1
        elif param[i].kind() == Kind.OTHER or param[i].kind() == Kind.LENGTH_CONSTRAINT:
            recursivelyFindRegexOrWEQ(param[i].children(), WEQ, RGX, numLenCon)
    return


def getMaxRecDepth(node):
    if len(node.children()) == 0:
        return 1
    else:
        maxdepth = 0
        for child in node.children():
            maxdepth = max(maxdepth, getMaxRecDepth(child))
        return maxdepth + 1

def extract(ast):
    l = ast.get_intel()
    v = l["variables"]
    stringVars = []
    allVars = []
    for elem in v.keys():
        if str(elem).find('String') > 0:
            for el in v[elem]:
                stringVars.append(el)
                allVars.append(el)
        else:
            for el in v[elem]:
                allVars.append(el)
    #print(stringVars)
    #print(allVars)

    WEQ = []
    RGX = []
    numLenCon = [0]
    numAsserts = len(ast)
    maxRecDepth = 0

    for node in ast:
        RecDepth = getMaxRecDepth(node)
        if RecDepth > maxRecDepth:
            maxRecDepth = RecDepth
        if node.kind() == Kind.WEQ:
            children = node.children()
            lhs = children[0]
            rhs = children[1]
            left = []
            left = extractWEQ(lhs, left)
            right = []
            right = extractWEQ(rhs, right)
            if len(left) < 1:
                left = [('', 0, 0)]
            if len(right) < 1:
                right = [('', 1, 0)]

            lhs = left[0][0]  #erster eintrag der linken seite
            lhsRange = [left[0][1]-1]  #startet bei 0 deswegen - 1
            lhsVars = [left[0][2]]  # gibt an ob es eine variable ist oder nicht

            rhs = right[0][0]  # erster eintrag der rechten seite
            rhsRange = [right[0][1] - 1]  # startet bei 0 deswegen - 1
            rhsVars = [right[0][2]]  # gibt an ob es eine variable ist oder nicht

            for i in range(1, len(left)):
                lhs += left[i][0]
                lhsRange.append(lhsRange[i-1] + left[i][1])
                lhsVars.append(left[i][2])
            for i in range(1, len(right)):
                rhs += right[i][0]
                rhsRange.append(rhsRange[i-1] + right[i][1])
                rhsVars.append(right[i][2])

            eq = Equation()
            eq.LHS = lhs
            eq.RHS = rhs
            eq.endPointsLHS = lhsRange
            eq.endPointsRHS = rhsRange
            eq.isVarLHS = lhsVars
            eq.isVarRHS = rhsVars
            eq.displayText = lhs + " = " + rhs
            WEQ.append(eq)
        if node.kind() == Kind.REGEX_CONSTRAINT:
            rgx = ""
            rgx = exRE(node, rgx)
            RGX.append(rgx)
        if node.kind() == Kind.LENGTH_CONSTRAINT:
            numLenCon[0] += 1

        if node.kind() == Kind.OTHER:
            param = node.children()
            recursivelyFindRegexOrWEQ(param, WEQ, RGX, numLenCon)
    return allVars, stringVars, WEQ, RGX, numLenCon[0], numAsserts, maxRecDepth
