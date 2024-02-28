import math

from z3 import z3

from smtquery.extract.featureExtractionFiles.generalClasses import Equation
from smtquery.smtcon.exprfun import *
from smtquery.smtcon.expr import Kind
from automata.fa.nfa import NFA
from automata.fa.dfa import DFA
import string
UC = string.printable

def extractApproxStates(param):

    for i in range(len(param)):
        op = param[i].decl()

        if str(op) == "re.++":
            children = param[i].children()
            left = extractApproxStates([children[0]])
            right = extractApproxStates([children[1]])
            return left + right
        elif str(op) == "re.+":
            nfa = extractApproxStates(param[i].children())
            return nfa
        elif str(op) == "re.*":
            nfa = extractApproxStates(param[i].children())
            return nfa+1
        elif str(op) == "re.opt":
            nfa = extractApproxStates(param[i].children())
            return nfa + 1
        elif str(op) == "re.inter":
            nfa = extractApproxStates([param[i].children()[0]])
            nfa1 = extractApproxStates([param[i].children()[1]])
            return nfa * nfa1
        elif str(op) == "re.union":
            nfa = extractApproxStates([param[i].children()[0]])
            nfa1 = extractApproxStates([param[i].children()[1]])
            return nfa + nfa1 + 1
        elif str(op) == "re.comp":
            nfa = extractApproxStates(param[i].children())
            exp = math.sqrt(nfa* math.log(nfa))
            return math.exp(exp)
        elif str(op) == "re.none":
            return 1
        elif str(op) == "re.all":
            #all letters plus extra symbols
            return 100
        elif str(op) == "re.allchar":
            #all letters capital and not
            return 52
        elif str(op) == "re.diff":
            nfa1 = extractApproxStates([param[i].children()[0]])
            nfa2 = extractApproxStates([param[i].children()[1]])

            return nfa1 * nfa2
        elif str(op) == "re.range":
            w1 = str(param[i].children()[0])[1:-2]
            w2 = str(param[i].children()[1])[1:-2]
            if len(w1) > 1:
                w1 = 'a'
            if len(w2) > 1:
                w2 = 'z'
            a = ord(w2)+1 - ord(w1)
            return a + 1
        elif str(op) == "re.^":
            nfa1 = extractApproxStates(param[i].children())

            ran = int(param[i].vParams[0])
            tmp = nfa1 * ran
            return tmp

        elif str(op) == "re.loop":

            nfa1 = extractApproxStates(param[i].children())

            ran1 = int(param[i].vParams[0])
            ran2 = int(param[i].vParams[1])

            if ran2 < ran1:
                return 1
            elif ran1 == ran2:
                return nfa1 * ran1
            else:
                #*2 because of the union of the resulting nfa
                return nfa1 * ran2 * 2
        elif str(op) == "str.to_re":
            m = str(param[i].children()[0])[1:-2]

            return len(m) + 2
        else: return 0






def range_nfa(w1, w2):
    if len(w1) > 1:
        w1 = 'a'
    if len(w2) > 1:
        w2 = 'z'
    # Erstelle einen neuen NFA mit einem Start- und Akzeptierzustand
    #nfa = NFA(states={'q0', 'qf'}, input_symbols=set(UC), initial_state='q0', final_states={'qf'}, transitions={'q0': {'a': {'qf'}}})


    # Füge für jedes Zeichen im Bereich einen Zustand und einen Übergang hinzu
    a = (ord(w2) + 1) - ord(w1)

    states = set()
    states.add('q0')
    states.add('qf')
    final_states = set()
    final_states.add('qf')
    transitions = dict()
    transitions['q0'] = {}
    for c in range(ord(w1), ord(w2)+1):
        c = chr(c)
        transitions['q0'][c] = {}
        transitions['q0'][c] = {'qf'}
    return NFA(states=states, input_symbols=set(UC), initial_state='q0', final_states=final_states,
               transitions=transitions)


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



def extractChildren(param):

    for i in range(len(param)):
        op = param[i].decl()

        if str(op) == "re.++":
            children = param[i].children()
            left = extractChildren([children[0]])
            right = extractChildren([children[1]])
            return left.concatenate(right)
        elif str(op) == "re.+":
            nfa = extractChildren(param[i].children())

            new_states = set(nfa.states)
            new_initial_state = NFA._add_new_state(new_states)

            # Transitions are the same with a few additions.
            new_transitions = dict(nfa.transitions)
            new_transitions[new_initial_state] = {'': {nfa.initial_state}}
            for state in nfa.final_states:
                new_transitions[state] = dict(new_transitions.get(state, {}))
                transition = new_transitions[state]
                transition[''] = set(transition.get('', set()))
                transition[''].add(nfa.initial_state)

            nfa = nfa.__class__(
                states=new_states,
                input_symbols=nfa.input_symbols,
                transitions=new_transitions,
                initial_state=new_initial_state,
                final_states=nfa.final_states)

            return nfa

        elif str(op) == "re.*":
            nfa = extractChildren(param[i].children())
            nfa = nfa.kleene_star()
            return nfa
        elif str(op) == "re.opt":
            nfa = extractChildren(param[i].children())
            nfa1 = NFA.from_regex('')
            return nfa.union(nfa1)
        elif str(op) == "re.inter":
            nfa = extractChildren([param[i].children()[0]])
            nfa1 = extractChildren([param[i].children()[1]])
            return nfa.intersection(nfa1)
        elif str(op) == "re.union":
            nfa = extractChildren([param[i].children()[0]])
            nfa1 = extractChildren([param[i].children()[1]])
            return nfa.union(nfa1)
        elif str(op) == "re.comp":
            nfa = extractChildren(param[i].children())
            dfa = DFA.from_nfa(nfa).complement(minify=False)
            return NFA.from_dfa(dfa)
        elif str(op) == "re.none":
            # NFA-Objekt erstellen
            none_nfa = NFA(states={'q0'},input_symbols=set(),transitions={},initial_state='q0',final_states=set())
            return none_nfa
        elif str(op) == "re.all":
            states = {'q0'}
            input_symbols = set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789\\\"|+*/&%$')
            transitions = {'q0': {'': {'q0'}}}
            initial_state = 'q0'
            final_states = {'q0'}

            # NFA-Objekt erstellen
            all_nfa = NFA(states=states,input_symbols=input_symbols,transitions=transitions,initial_state=initial_state,final_states=final_states)
            return all_nfa
        elif str(op) == "re.allchar":
            states = {'q0'}
            input_symbols = set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789')
            transitions = {'q0': {symbol: {'q0'} for symbol in input_symbols}}
            initial_state = 'q0'
            final_states = {'q0'}
            # NFA-Objekt erstellen
            allchar_nfa = NFA(states=states,input_symbols=input_symbols,transitions=transitions,initial_state=initial_state,final_states=final_states)
            return allchar_nfa
        elif str(op) == "re.diff":
            nfa1 = extractChildren([param[i].children()[0]])
            nfa2 = extractChildren([param[i].children()[1]])
            dfa1 = DFA.from_nfa(nfa1, minify=False)
            dfa2 = DFA.from_nfa(nfa2, minify=False)
            res = dfa1.difference(dfa2)
            return NFA.from_dfa(res)
        elif str(op) == "re.range":
            w1 = str(param[i].children()[0])[1:-2]
            w2 = str(param[i].children()[1])[1:-2]
            return range_nfa(w1, w2)
        elif str(op) == "re.^":
            nfa1 = extractChildren(param[i].children())

            ran = int(param[i].vParams[0])
            tmp = nfa1.copy()
            for i in range(ran):
                tmp = tmp.concatenate(nfa1)
            return tmp

        elif str(op) == "re.loop":

            nfa1 = extractChildren(param[i].children())

            ran1 = int(param[i].vParams[0])
            ran2 = int(param[i].vParams[1])

            if ran2 < ran1:
                none_nfa = NFA(states={'q0'}, input_symbols=set(), transitions={}, initial_state='q0',
                               final_states=set())
                return none_nfa
            elif ran1 == ran2:
                tmp = nfa1.copy()
                for i in range(ran1):
                    tmp = tmp.concatenate(nfa1)
                return tmp
            else:
                nfas = []
                tmp = nfa1.copy()
                for i in range(ran1):
                    tmp = tmp.concatenate(nfa1)
                nfas.append(tmp.copy())
                for j in range(ran1+1, ran2):
                    tmp = tmp.concatenate(nfa1)
                    nfas.append(tmp.copy())
                tmp = nfas[0]
                for k in range(1, len(nfas)):
                    tmp = tmp.union(nfas[k])
                return tmp
        elif str(op) == "str.to_re":
            m = str(param[i].children()[0])[1:-2]

            states = set()
            alphabet = set()
            start = 'q0'
            end = {'qf'}
            states.add('qf')
            transitions = dict()

            for i in range(len(m)):
                alphabet.add(m[i])
                states.add("q" + str(i))
                transitions['q' + str(i)] = {}
                transitions['q' + str(i)][m[i]] = {}
                transitions['q' + str(i)][m[i]] = {"q" + str(i + 1)}
            states.add("q" + str(len(m)))
            transitions['q' + str(len(m))] = {}
            transitions['q' + str(len(m))][''] = {"qf"}
            n = NFA(states=states, input_symbols=alphabet, initial_state='q0', final_states=end,
                    transitions=transitions)
            return n
        else: return None




def recursivelyFindRegexOrWEQ(param, WEQ, RGX, numLenCon, RGXDepth):
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
            RGXDepth.append(getMaxRecDepth(param[i]))
            rgx = extractChildren(param[i].children()[1:])
            #rgx = NFA(states={'q0'},input_symbols=set(),transitions={},initial_state='q0',final_states=set())
            RGX.append(rgx)
            #return
        elif param[i].kind() == Kind.LENGTH_CONSTRAINT:

            numLenCon[0] += 1
        elif param[i].kind() == Kind.OTHER or param[i].kind() == Kind.LENGTH_CONSTRAINT:
            recursivelyFindRegexOrWEQ(param[i].children(), WEQ, RGX, numLenCon, RGXDepth)
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


    WEQ = []
    RGX = []
    RGXDepth = []
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
            #rgx = NFA(states={'q0'},input_symbols=set(),transitions={},initial_state='q0',final_states=set())
            rgx = extractChildren(node.children()[1:])
            RGXDepth.append(getMaxRecDepth(node))
            RGX.append(rgx)
        if node.kind() == Kind.LENGTH_CONSTRAINT:
            numLenCon[0] += 1

        if node.kind() == Kind.OTHER:
            param = node.children()
            recursivelyFindRegexOrWEQ(param, WEQ, RGX, numLenCon, RGXDepth)
    return allVars, stringVars, WEQ, RGX, numLenCon[0], numAsserts, maxRecDepth, RGXDepth

