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