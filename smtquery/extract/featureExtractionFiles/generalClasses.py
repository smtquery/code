class Equation:
    LHS = ""
    RHS = ""
    ID = 0
    displayText = ""
    group = 0
    endPointsLHS = []
    isVarLHS = []
    endPointsRHS = []
    isVarRHS = []
class Node:
    displayText = ""
    group = 0
    LHS = ""
    RHS = ""
class Edge():
    origin = Node()
    to = Node()
    usedRule = ""

