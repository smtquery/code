class Variable:
    v = None

    def __init__(self, v):
        self.v = v

    def __repr__(self):
        return f'Var: {self.v}'

class Pattern:
    vs = []
    def __init__(self, vs):
        self.vs = vs

    def __repr__(self):
        return f'Pat: {self.vs}'

class Matching:
    v = None
    vs = []
    def __init__(self, v, vs):
        self.v = v
        self.vs = vs

    def valid(self):
        return self.v not in self.vs

    def __repr__(self):
        return f'{self.v}:{self.vs}'
