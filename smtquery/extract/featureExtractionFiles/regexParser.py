import pythomata
import stopit
from smtquery.extract.featureExtractionFiles.extractMinDFA import extractMinDFA
import copy
reg = ""


def extractChildren(param):
    reg = ""
    '''if str(param).startswith("Range("):
        tmp = str(param).replace("Range(", "")
        tmp = tmp.replace("\")", "")
        tmp = tmp.replace("\"", "")
        tmp = tmp.replace(",", "")
        tmp = tmp.split(" ")
        reg += tmp[0] + "-" + tmp[1]

        return reg
    if str(param).startswith("Re(\""):
        tmp = str(param).replace("Re(\"", "")
        tmp = tmp[0:-2]
        reg += tmp[0]

        return reg
    if str(type(param)) != "<class 'list'>" and str(type(param)) != "<class 'z3.z3.ReRef'>":

        if str(type(param)) == "<class 'z3.z3.SeqRef'>":
            if str(param).startswith("IntToStr") or str(param).startswith("StrToInt"):
                tmp = str(param).replace("IntToStr(", "")
                tmp = tmp.replace("StrToInt(", "")
                tmp = tmp[0:len(tmp)-1]
                reg += tmp

                return reg
            return str(param)[1:len(str(param))-1]
        reg += str(param)
        return reg'''
    for i in range(len(param)):
        op = param[i].decl()
        if str(op) == "re.++":
            reg += extractChildren(param[i].children())
            #for child in param[i].children():
            #   reg += extractChildren(child.children())
        elif str(op) == "Plus":
            reg += "(" + extractChildren(param[i].children()) + ")+"
        elif str(op) == "Star":
            reg += "(" + extractChildren(param[i].children()) + ")*"
        elif str(op) == "Re":
            reg += extractChildren(param[i].children())
        elif str(op) == "String":
            m = str(param[i])
            hasEscape = False
            if m[1] == "\\":
                hasEscape = True
                m = m[1:]
                #m = "\\" + m
                if m[len(m)-2] == "\\":
                    m = m[len(m)-2]
                else:
                    m = m[:len(m) - 1]
            if m[len(m) - 2] == "\\":
                hasEscape = True

            if hasEscape:
                m =  m[0:len(str(param[i]))]
                reg += m
                reg = reg.replace("(", "l").replace(")","l")
            else:
                reg += str(param[i])[1:len(str(param[i]))-1].replace("(", "l").replace(")","l")
        elif str(op) == "IntToStr":
            reg += extractChildren(param[i].children())
        elif str(op) == "Union":
            p1 = param[i].children()[0]
            b = []
            b.append(p1)
            b1 = []
            p2 = param[i].children()[1]
            b1.append(p2)
            reg += "(" + extractChildren(b) + ")(" + extractChildren(b1) + ")" + "|"
        elif str(op) == "Range":
            tmp = str(param[0]).replace("Range(", "")
            tmp = tmp.replace("\")", "")
            tmp = tmp.replace("\"", "")
            tmp = tmp.replace(",", "")
            tmp = tmp.split(" ")
            reg += tmp[0] + "-" + tmp[1]
        elif str(op) == "re.allchar":
            reg = "a-zA-Z"
        elif str(type(op)) == "<class 'z3.z3.FuncDeclRef'>":
            k = param[0]
            reg += str(param[0])
    return reg


def extractReg(param, rgx):
    op = param.decl()
    if str(op) == "InRe":
        reg = extractChildren(param.children()[1:])
        rgx.append(reg)
        return rgx
    param = param.children()
    for i in range(len(param)):
        op = param[i].decl()
        if str(op) == "InRe":
            reg = extractChildren(param[i].children()[1:])
            rgx.append(reg)
    return rgx


def extractNumSymb(reg):
    num = 0
    for i in reg:
        if i != ")" and i != "(" and i != "+" and i != "*" and i != "|":
            num += 1
    return num


def extractDepth(reg):
    depth = 0
    tmpDepth = 0
    for i in reg:
        if i == "(":
            tmpDepth += 1
        if i == ")":
            if tmpDepth >= depth:
                depth = tmpDepth
            tmpDepth -= 1
    return depth

@stopit.threading_timeoutable(timeout_param='my_timeout')
def getMinDFA(nfa, states, alphabet, start, final, transition, timeout="whatever"):
    try:
        dfa = pythomata.SimpleDFA(states, alphabet, start, final, transition)
        d = copy.deepcopy(dfa)
        mindfa = dfa.minimize()
        return d, mindfa
    except stopit.utils.TimeoutException:
        return nfa, nfa





def extractNumStates(rg):
    if len(rg) <= 1:  # automatic toolkit makes minDFA to 1 states from single letter Regex
        return 2,3,3
    else:
        nfa, states, alphabet, start, final, transition = extractMinDFA(rg)
        dfa, dfaMin = getMinDFA(nfa, states, alphabet, start, final, transition, my_timeout=300)
        return len(nfa.states), len(dfa.states), len(dfaMin.states)

def extractFeat(RGX):

    maxSymb = 0
    maxDepth = 0
    maxNumState = 0
    for reg in RGX:
        tmpSymb = extractNumSymb(reg)
        tmpDepth = extractDepth(reg)
        _,_,tmpNumState = extractNumStates(reg)
        print(tmpNumState)
        if tmpSymb >= maxSymb:
            maxSymb = tmpSymb
        if tmpDepth >= maxDepth:
            maxDepth = tmpDepth
        if tmpNumState >= maxNumState:
            maxNumState = tmpNumState

    return maxSymb, maxDepth, maxNumState

