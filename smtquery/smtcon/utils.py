class Variable:
    v = None

    def __init__(self, v):
        self.v = v

class Pattern:
    vs = []
    def __init__(self, vs):
        self.vs = vs

class Matching:
    v = None
    vs = []
    def __init__(self, v, vs):
        self.v = v
        self.vs = vs

    def valid(self):
        return self.v not in self.vs


class NonMatching:
    def valid(self):
        return False
