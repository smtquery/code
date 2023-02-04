import pythomata
from automata_tools import BuildAutomata
import copy

import smtquery.extract.featureExtractionFiles.regToNFA as regToNFA


def constructGraph(currentIdx, reg):
    automata = []
    while currentIdx < len(reg):
        char = reg[currentIdx]
        if char != "(" and char != ")" and char != "+" and char != "|" and char != "*":
            automata.append(BuildAutomata.characterStruct(char))
            if len(automata) > 1:
                a = automata.pop()
                b = automata.pop()
                automata.append(BuildAutomata.concatenationStruct(b, a))
        elif char == "*":
            auto = automata.pop()
            return BuildAutomata.starStruct(auto), currentIdx
        elif char == "|":
            a = automata.pop()
            b = automata.pop()
            return BuildAutomata.unionStruct(b, a), currentIdx
        elif char == "+":
            a = automata.pop()
            automata.append(BuildAutomata.starStruct(a))
            b = automata.pop()
            return BuildAutomata.concatenationStruct(a, b), currentIdx
        elif char == "(":
            if len(automata) >= 1:
                a = automata.pop()
                currentIdx += 1
                b, i = constructGraph(currentIdx, reg)
                automata.append(BuildAutomata.concatenationStruct(a, b))
                currentIdx = i
            else:
                currentIdx += 1
                b, i = constructGraph(currentIdx, reg)
                automata.append(b)
                currentIdx = i
        elif char == ")" and reg[currentIdx+1] == "(":
            a = automata.pop()
            b, i = constructGraph(currentIdx + 2, reg)
            currentIdx = i
            return BuildAutomata.unionStruct(a, b), currentIdx
        elif char == ")" and reg[currentIdx+1] == "|":
            a = automata.pop()
            return a, currentIdx+1
        currentIdx += 1

def extractMinDFA(rg):
    automata =  []
    rg = rg.replace("e", "1") # e is the epsilon in a subsequent tool
    rg = rg.replace("\\", "2") # this is an escape symbol
    rg = rg.replace(" ", "3")

    ind = 0
    while ind in range(len(rg)):
        char = rg[ind]
        if char != "(" and char != ")" and char != "+" and char != "|" and char != "*" and char != ".":
            automata.append(BuildAutomata.characterStruct(char))
            if len(automata) > 1:
                a = automata.pop()
                b = automata.pop()
                automata.append(BuildAutomata.concatenationStruct(b, a))
        elif char == "(":
            if len(automata) >= 1:
                a = automata.pop()
                ind += 1
                b, i = constructGraph(ind, rg)
                automata.append(BuildAutomata.concatenationStruct(a, b))
                ind = i
            else:
                ind += 1
                a, i = constructGraph(ind, rg)
                automata.append(a)
                ind = i
        ind += 1



    while len(automata) > 1:
        a = automata.pop()
        b = automata.pop()
        automata.append(BuildAutomata.concatenationStruct(b, a))
    l = automata[0]



    transitions = []
    lang = []
    for trans in l.transitions:
        current = []
        for tr in l.transitions[trans]:
            for t in l.transitions[trans][tr]:
                transitions.append([str(trans), str(t), str(tr)])
    for t in transitions:
        if t[1] == "\u03B5":
            t[1] = 'e'
        else:
            if t[1] not in lang:
                lang.append(t[1])
    finalS = []
    for elem in l.finalstates:
        finalS.append(str(elem))

    nfa = regToNFA.NFA(len(l.states), list(map(str, l.states)), len(lang), lang, str(l.startstate), len(l.finalstates),finalS, len(transitions),  transitions)
    dfa = regToNFA.nfaTOdfa(nfa)

    start = ''
    states = set([])
    final = set([])
    alphabet = set([])
    transition = {}
    i = 0
    lines = dfa.source.split("\n")

    while i < len(lines)-1:
        if lines[i].find("node") > 0:
            state = lines[i+1].split()[0]
            if state != '""':
                states.add(state)
            if state == '""':
                start = lines[i + 2].split()[2]
                states.add(start)
            if lines[i].find("doublecircle") > 0:
                if state not in final:
                    final.add(state)
        elif len(lines[i].split()) == 4:
            line = lines[i].split()
            f = line[0]
            t = line[2]
            label = line[3].replace("[label=", "").replace("]", "")
            if label.startswith("\""):
                if label != '"\u03A6"':
                    label = label.replace("\"", "")
                    alphabet.update(label)
            else:
                alphabet.update(label)
            if transition.get(f) is None:
                transition.update({f : {label : t}})
            else:
                tmp = transition.get(f)
                tmp.update({label : t} )
        i += 1

    return nfa, states, alphabet, start, final, transition