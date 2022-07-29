import enum

class Trool(enum.Enum):
    TT = 0
    FF = 1
    Maybe = 2

def TroolNot(t):
    if t == Trool.TT:
        return Trool.FF
    elif t == Trool.FF:
        return Trool.TT
    elif t == Trool.Maybe:
        return Trool.Maybe

def TroolAnd(t1,t2):
    if t1 == Trool.TT and t2 == Trool.TT:
        return Trool.TT
    elif t1 == Trool.FF or t2 == Trool.FF:
        return Trool.FF
    elif t1 == Trool.Maybe and t2 == Trool.Maybe:
        return Trool.Maybe


def TroolOr(t1,t2):
    if t1 == Trool.TT or t2 == Trool.TT:
        return Trool.TT
    elif t1 == Trool.FF and t2 == Trool.FF:
        return Trool.FF
    elif t1 == Trool.Maybe or t2 == Trool.Maybe:
        return Trool.Maybe