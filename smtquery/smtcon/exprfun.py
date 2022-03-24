import hashlib
import itertools
import math
import smtquery.utils.pattern

from smtquery.smtcon.expr import *

class ExprFun:
    def __init__(self,name,version):
        self._name = name
        self._version = version
    def getName (self):
        return self._name
    def getVersion (self):
        return self._version
    def apply (self, expr, data):
        return None
    def merge(self, expr, data1, data2):
        return None


class AssertTrue(ExprFun):
    def __init__(self):
        super().__init__('AssertTrue', '0.0.2')

    def apply(self, expr, data):
        if expr.decl() == '=' and 'true' in [str(x) for x in expr.children()]:
            data += 1
        return data

    def merge(self, expr, data):
        return sum(data)


class TerminalLengths(ExprFun):
    def __init__(self):
        super().__init__('TerminalLengths', '0.0.1')

    def apply(self, expr, data):
        print(expr)
        if expr.is_const() and expr.sort() == Sort.String:
            l = len(expr.params()[0])-2
            data += [l]
        return data

    def merge(self, expr, data):
        d_new = []
        for d in data:
            d_new += d
        return d_new

class HashConstraints(ExprFun):
    def __init__(self):
        super().__init__('HashConstraints', '0.0.1')

    def apply(self, expr, data):
        if expr.kind() != Kind.CONSTANT and expr.kind() != Kind.VARIABLE:
            h = hashlib.md5(repr(expr).encode('utf-8')).hexdigest()
            print(expr, h)
            if h not in data:
                data[h] = 0
            data[h] += 1
        return data

    def merge(self, expr, data):
        d_new = dict()
        for d in data:
            for k, v in d.items():
                if k not in d_new:
                    d_new[k] = 0
                d_new[k] += v

        return d_new

class Bounded(ExprFun):
    def __init__(self):
        super().__init__('Bounded', '0.1.0')

    # data = [dict(),...]
    def apply(self, expr, data):
        if expr.kind() == Kind.WEQ:
            v, c, w = None, None, None
            for e in expr.children():
                if e.is_variable() and not v:
                    v = str(e)
                elif e.is_variable() and v:
                    w = str(e)
                elif e.is_const():
                    c = len(str(e))-2
            if v and c:
                if len(data) == 0:
                    data += [dict()]
                for d in data:
                    if 'weq' not in d:
                        d['weq'] = dict()
                    d['weq'][v] = (c, c)
            elif v and w:
                if len(data) == 0:
                    data += [dict()]
                for d in data:
                    if 'rel' not in d:
                        d['rel'] = dict()
                    d['rel'][v] = [('=', w)]
                    d['rel'][w] = [('=', v)]
        elif expr.kind() == Kind.LENGTH_CONSTRAINT:
            v, c, w = None, None, None
            ci = 0
            for i, e in enumerate(expr.children()):
                if e.is_const():
                    c = int(str(e))
                    ci = i
                elif e.kind() == Kind.OTHER and e.decl() == 'str.len':
                    if not v:
                        v = str(e.children()[0])
                    else:
                        w = str(e.children()[0])
            if v and c is not None:
                if len(data) == 0:
                    data += [dict()]
                for d in data:
                    if 'lc' not in data:
                        d['lc'] = dict()
                    if (expr.decl() == '<' and ci == 1) or (expr.decl() == '>' and ci == 0):
                        d['lc'][v] = (0, c-1)
                    elif (expr.decl() == '>' and ci == 1) or (expr.decl() == '<' and ci == 0):
                        d['lc'][v] = (c+1, float('inf'))
                    elif (expr.decl() == '<=' and ci == 1) or (expr.decl() == '>=' and ci == 0):
                        d['lc'][v] = (0, c)
                    elif (expr.decl() == '>=' and ci == 1) or (expr.decl() == '<=' and ci == 0):
                        d['lc'][v] = (c, float('inf'))
                    elif expr.decl() == '=':
                        d['lc'][v] = (c, c)
            elif v and w:
                if len(data) == 0:
                    data += [dict()]
                for d in data:
                    if 'rel' not in data:
                        d['rel'] = dict()
                    # invariant: (op (str.len v) (str.len w))
                    if expr.decl() == '<':
                        d['rel'][v] = [('<', w)]
                        d['rel'][w] = [('>', v)]
                    elif expr.decl() == '>':
                        d['rel'][v] = [('>', w)]
                        d['rel'][w] = [('<', v)]
                    elif expr.decl() == '<=':
                        d['rel'][v] = [('<=', w)]
                        d['rel'][w] = [('>=', v)]
                    elif expr.decl() == '>=':
                        d['rel'][v] = [('>=', w)]
                        d['rel'][w] = [('<=', v)]

        return data

    def merge(self, expr, data):
        # implement branching
        if isinstance(expr, ExprRef) and expr.decl() == 'ite':
            d_cond = data.pop(0)
            d_ret = []
            for dd in data.pop(0):
                for d in d_cond:
                    d_ret += [self._mergeDicts(d, dd)]
            for dd in data.pop(0):
                for d in self._negateDicts(d_cond):
                    d_ret += [self._mergeDicts(d, dd)]
            return d_ret
        if isinstance(expr, ExprRef) and expr.decl() == 'or':
            return [d for path in data for d in path]
        # demorgan
        if isinstance(expr, ExprRef) and expr.decl() == 'not':
            return self._negateDicts(data[0])

        d_ret = data.pop(0) if len(data) > 0 else dict()
        while len(data) > 0:
            d_tmp = []
            d_n = data.pop(0)
            if len(d_ret) == 0:
                d_tmp = d_n
            elif len(d_n) == 0:
                d_tmp = d_ret
            else:
                for d in d_ret:
                    for dd in d_n:
                        d_tmp += [self._mergeDicts(d, dd)]
            d_ret = d_tmp
        return d_ret

    def _mergeDicts(self, d1, d2):
        r_data = dict()
        for k in set(d1.keys()).union(set(d2.keys())):
            r_data[k] = dict()
        for t in ['lc', 'weq']:
            if t in set(d1.keys()).intersection(set(d2.keys())):
                for k in set(d1[t].keys()).union(set(d2[t].keys())):
                    if k in d1[t] and k in d2[t]:
                        # check interval overlap
                        l1, u1 = d1[t][k]
                        l2, u2 = d2[t][k]
                        if l1 <= u2 and l2 <= u1:
                            r_data[t][k] = (max(l1, l2), min(u1,u2))
                        else:
                            # if no overlap then length constraint is unsat
                            r_data[t][k] = (float('inf'), float('inf'))
                    elif k in d2[t]:
                        r_data[t][k] = d2[t][k]
                    elif k in d1[t]:
                        r_data[t][k] = d1[t][k]
            elif t in d1.keys():
                r_data[t] = d1[t]
            elif t in d2.keys():
                r_data[t] = d2[t]
        if 'rel' in set(d1.keys()).intersection(set(d2.keys())):
            for k in set(d1['rel'].keys()).union(set(d2['rel'].keys())):
                if k in d1['rel'] and k in d2['rel']:
                    for l1 in d1['rel'][k]:
                        for l2 in d2['rel'][k]:
                            op1, v = l1
                            op2, w = l2
                            r_data['rel'][k] = []
                            if v == w and ({op1, op2} == {'=', '>='} or {op1, op2} == {'=', '<='}):
                                r_data['rel'][k] += [('=', v)]
                            elif v == w and {op1, op2} == {'>', '>='}:
                                r_data['rel'][k] += [('>', v)]
                            elif v == w and {op1, op2} == {'<', '<='}:
                                r_data['rel'][k] += [('<', v)]
                elif k in d1['rel']:
                    r_data['rel'][k] = d1['rel'][k]
                elif k in d2['rel']:
                    r_data['rel'][k] = d2['rel'][k]
        elif 'rel' in d1.keys():
            r_data['rel'] = d1['rel']
        elif 'rel' in d2.keys():
            r_data['rel'] = d2['rel']
        return r_data

    # currently only single bound dicts can be negated
    def _negateDicts(self, ds):
        r_data = []
        # negate every term
        d_news = []
        for d in ds:
            d_new = []
            if 'lc' in d.keys():
                for k, v in d['lc'].items():
                    l, u = v
                    if l != 0:
                        d_new += [{'lc': {k: (0, l - 1)}}]
                    if u != float('inf'):
                        d_new += [{'lc': {k: (u + 1, float('inf'))}}]
                    if l == 0 and u == float('inf'):
                        d_new += [{'lc': {k: (float('inf'), float('inf'))}}]
                d_news.append(d_new)
            if 'rel' in d.keys():
                for k, v in d['rel'].items():
                    for op, w in v:
                        if op == '<':
                            d_new.append({'rel': {k: [('>=', w)], w: [('<=', k)]}})
                        elif op == '<=':
                            d_new.append({'rel': {k: [('>', w)], w: [('<', k)]}})
                        elif op == '>':
                            d_new.append({'rel': {k: [('<=', w)], w: [('>=', k)]}})
                        elif op == '>=':
                            d_new.append({'rel': {k: [('<', w)], w: [('>', k)]}})
                d_news.append(d_new)
        if len(d_news) > 0:
            for con in itertools.product(*d_news):
                res = con[0]
                for d in con[1:]:
                    res = self._mergeDicts(res, d)
                r_data += [res]
        return r_data


class Fragments(ExprFun):

    _q = {'forall', 'exists'}
    _lia = {'+', '-', '*', '>', '<', 'abs'}
    _nlia = {'div', 'mod'}
    _ra = {'/', 'to_real'}

    def __init__(self):
        super().__init__('Fragments', '0.0.1')

    def apply(self, expr, data):
        # determine fragment for current node
        if expr.decl() in self._q:  # quantified term
            return False, 0
        elif expr.decl() in self._ra:  # term with reals arithmetic
            return True, 3
        elif expr.decl() in self._nlia:  # term with non linear integer arithmetic
            return True, 2
        elif expr.decl() in self._lia or expr.sort() == Sort.Int:  # term with linear integer arithmetic
            return True, 1
        else:
            return True, 0

    def merge(self, expr, data):
        # select least restrictive fragment
        print(data)
        qf = True
        mx = 0
        for q, l in data:
            qf &= q
            mx = max(mx, l)

        print(qf, mx)
        return qf, mx

class PatternMatching(ExprFun):
    def __init__(self):
        super().__init__('PatternMatching', '0.0.2')

    def apply(self, expr, data):
        if data == 'non_matching':
            return 'non_matching'
        if expr.is_variable():
            if isinstance(data, smtquery.utils.pattern.Pattern):
                return smtquery.utils.pattern.Pattern(data.vs + [str(expr)])
            return smtquery.utils.pattern.Variable(str(expr))
        elif expr.is_const():
            if isinstance(data, smtquery.utils.pattern.Pattern):
                return smtquery.utils.pattern.Pattern(data.vs)
            return smtquery.utils.pattern.Pattern([])
        elif expr.kind() == Kind.WEQ:
            assert len(data) == 2
            l, r = data
            if not isinstance(l, (smtquery.utils.pattern.Pattern, smtquery.utils.pattern.Variable)) or not isinstance(r, (smtquery.utils.pattern.Pattern, smtquery.utils.pattern.Variable)):
                return 'non_matching'
            else:
                return [l,r]
            # old
            '''
            v, vs = None, None
            for d in data:
                if isinstance(d, utils.Variable):
                    if v and vs:
                        vs += [d.v]
                    elif v:
                        vs = [d.v]
                    else:
                        v = d.v
                elif isinstance(d, utils.Pattern):
                    vs = d.vs
            if v is None or vs is None or v in vs:
                return 'non_matching'
            return utils.Matching(v, vs)
            '''
        elif expr.kind() == Kind.OTHER and expr.decl() == 'str.++':
            vs = []
            for d in data:
                if isinstance(d, smtquery.utils.pattern.Variable):
                    vs += [d.v]
                elif isinstance(d, smtquery.utils.pattern.Pattern):
                    vs += d.vs
            return smtquery.utils.pattern.Pattern(vs)
        elif expr.kind() == Kind.OTHER and expr.decl() == 'and':
            return data
        return 'non_matching'

    def merge(self, expr, data):
        # workaround for and-concat of weqs
        #if len(data) == 1:
        #    return data[0]
        # if 'non_matching' in data:
        #     return 'non_matching'
        return data

class RegExLengths(ExprFun):
    def __init__(self):
        super().__init__('RegExLengths', '0.0.1')

    def apply(self, expr, data):
        if expr.sort() == Sort.RegEx:
            if expr.decl() == 'str.to_re':
                return len(str(expr.children()[0]))-2
            if expr.decl() in ['re.*', 're.+']:
                return data[0] + 1
            if expr.decl() in ['re.range', 're.allchar']:
                return 1
            else:
                return data
        elif len(data) != 0:
            return data[0]
        else:
            return 0


    def merge(self, expr, data):
        if isinstance(expr, ReExpr):
            if expr.decl() == 're.++':
                return sum(data)
            elif expr.decl() == 're.union':
                return sum(data)
            elif expr.decl() == 're.inter':
                return sum(data)
        return list(filter(lambda e: e != [] and e != 0, data))

class Degree(ExprFun):
    def __init__(self):
        super().__init__('Degree', '0.0.1')

    def apply(self, expr, data):
        pass

    def merge(self, expr, data):
        pass

class HasAtom(ExprFun):
    def __init__(self):
        super().__init__ ("HasAtom","0.0.1")
        
    def apply (self, expr, data):
        if expr.kind() not in data:
            data[expr.kind()] = 0
        data[expr.kind()]+=1
        return data

    def merge(self, expr, data):
        d_new = dict()
        for d in data:
            for k in set(d_new.keys()).union(set(d.keys())):
                if k in d_new and k in d:
                    d_new[k]+=d[k]
                elif k in d:
                    d_new[k] = d[k]
        return d_new

class VariableCount(ExprFun):
    def __init__(self):
        super().__init__ ("VariableCount","0.0.1")
        
    def apply (self, expr, data):
        if expr.is_variable():
            sort = expr.sort()
            decl = str(expr.decl())
            if sort not in data:
                data[sort] = dict()
            if decl not in data[sort]:
                data[sort][decl] = 0
            data[sort][decl]+=1
        return data

    def merge(self,expr,data):
        d_new = dict()
        for d in data:
            for t in set(d_new.keys()).union(set(d.keys())):
                if t not in d_new.keys():
                    d_new[t] = d[t]
                elif t in d.keys():
                    for v in set(d_new[t].keys()).union(set(d[t].keys())):
                        if v not in d_new[t]:
                            d_new[t][v] = 0
                        if v in d_new[t] and v in d[t]:
                            d_new[t][v]+=d[t][v]
        return d_new

class VariableCountPath(ExprFun):
    def __init__(self):
        super().__init__ ("VariablePath","0.0.1")
    
    # data = [dict(),...]
    def apply (self, expr, data):
        if expr.is_variable():
            sort = expr.sort()
            decl = str(expr.decl())
            if len(data) == 0:
                data+=[dict()]
            for d in data:
                if sort not in d:
                    d[sort] = dict()
                if decl not in d[sort]:
                    d[sort][decl] = 0
                d[sort][decl]+=1
        return data

    def merge(self,expr,data):
        ### branching for ite is missing!
        # we have to merge the first child with the second AND the third
        # but this function is called independently for each child
        if isinstance(expr,ExprRef) and expr.decl() == "ite":
            assert(len(data) == 3)
            d_cond = data.pop(0)
            d_ret = []
            for stmt in data:
                for dd in stmt:
                    for d in d_cond:
                        d_ret+=[self._mergeDicts(d,dd)]
            return d_ret

        if isinstance(expr,ExprRef) and expr.decl() == "or":
            return [d for path in data for d in path]

        d_ret = data.pop(0) if len(data) > 0 else dict()
        while len(data) > 0:
            d_tmp = []
            d_n = data.pop(0)
            if len(d_ret) == 0:
                d_tmp = d_n
            elif len(d_n) == 0:
                d_tmp = d_ret
            else:
                for d in d_ret:
                    for dd in d_n:
                        d_tmp+=[self._mergeDicts(d,dd)]
            d_ret = d_tmp
        return d_ret



        """data = []
        if len(data1) == 0:
            return data2
        elif len(data2) == 0:
            return data1
        for d1 in data1:
            for d2 in data2:
                data+=[self._mergeDicts(d1,d2)]
        return data
        """
    def _mergeDicts(self,d1,d2):
        r_data = dict()        
        for k in set(d1.keys()).union(set(d2.keys())):
            if k in d1 and k in d2:
                if isinstance(d1[k],int): 
                    r_data[k] = d1[k]+d2[k]
                else:
                    r_data[k] = self._mergeDicts(d1[k],d2[k])
            elif k in d2:
                r_data[k] = d2[k] if isinstance(d2[k],int) else d2[k].copy()
            elif k in d1: 
                r_data[k] = d1[k] if isinstance(d1[k],int) else d1[k].copy()
        return r_data


class RegexStructure(ExprFun):
    ere_sequences = [["re.comp", "Star", "re.comp"], ["re.comp", "Plus", "re.comp"], ["Intersect", "Plus"],
                     ["Intersect", "Star"]]

    def __init__(self):
        super().__init__("RegexStructure", "0.0.1")

    def apply(self, expr, data):
        if expr.decl() != "str.in_re":
            return data

        pat, regex = expr.children()[0], expr.children()[1]

        concatenation = not (self._isSimplePattern(pat) or pat.is_variable())

        complement = False
        paths = self._getAllPaths(self._buildRegLanGraph(regex), (0, regex.decl()))
        for seq in self.ere_sequences:
            if complement:
                break
            for p in paths:
                pp = [str(c) for c in p if str(c) in seq]
                complement = self._sublist(seq, pp)
                if complement:
                    break

        if "concatenation" in data:
            data = {"concatenation": concatenation or data["concatenation"],
                    "complement": complement or data["complement"]}
        else:
            data = {"concatenation": concatenation, "complement": complement}
        return data

    def merge(self, expr, data):
        data_new = {"concatenation": False, "complement": False}
        for d in data:
            if "concatenation" in d:
                data_new = {"concatenation": d["concatenation"] or data_new["concatenation"],
                            "complement": d["complement"] or data_new["complement"]}
        return data_new

    # pattern analysis
    def _isSimplePattern(self, expr, sp=True):
        if len(expr.children()) > 0:
            if expr.decl() in ["str.substr"]:
                return False
            if expr.decl() not in ["At"]:
                for c in expr.children():
                    sp = sp and self._isSimplePattern(c)
        else:
            sp = sp and expr.is_const()
        return sp

    # regex analysis
    def _buildRegLanGraph(self, regex, idx=0):
        edges = dict()
        if len(regex.children()) > 0:
            v1 = regex.decl()
            thisIdx = idx
            edges[(thisIdx, v1)] = set()
            for v2 in regex.children():
                idx += 1
                edges[(thisIdx, v1)].add((idx, v2.decl()))
                edges = {**edges, **self._buildRegLanGraph(v2, idx)}  # edges | buildRegLanGraph(v2,idx)
        return edges

    def _getAllPaths(self, graph, start):
        paths = []
        waiting = [[start]]
        while len(waiting) > 0:
            p = waiting.pop()
            v1 = p[-1]
            if v1 in graph:
                # it does not contain cycles!!!
                for v2 in graph[v1]:
                    waiting += [p + [v2]]
            else:
                paths += [[x[1] for x in p]]
        return paths

    def _sublist(self, lst1, lst2):
        return len(lst2) >= len(lst1) and [element for element in lst2 if element in lst1] == [element for element in
                                                                                               lst1 if element in lst2]


class Plot(ExprFun):
    def __init__(self):
        super().__init__ ("Plot","0.0.1")    

    # data = {"dot" : dot, succ : successor node ids, colours : label -> colour}
    def apply (self, expr, data):
        label = expr.decl()
        if expr.is_variable() or expr.is_const():
            label = f"{expr}"
        if label not in data["colours"]:
            data["colours"][label] = self._getNewColour([data["colours"][l] for l in data["colours"]])
        data["dot"].node(name=f"{expr.id()}", label=f"{label}", style='filled,rounded', shape="rectangle", color=f"{data['colours'][label][0]}", fontcolor=f"{data['colours'][label][1]}")
        data["succ"]=[expr.id()]
        return data

    def merge(self,expr,data):
        d_new = dict()
        for d in data:
            if len(d_new) == 0:
                d_new["dot"] = d["dot"]
                d_new["succ"] = []
                d_new["colours"] = d["colours"]

            if len(d['succ']) > 0 and expr.id() != d['succ'][0] and expr.id() != 0: # skip root node
                d_new["dot"].edge(f"{expr.id()}", f"{d['succ'][0]}",penwidth="0.5",arrowhead="none")  
        return d_new

    # auxilary functions
    def _colourGen(self):
        import random
        r = lambda: random.randint(0,255)
        c_r,c_g,c_b = r(),r(),r()
        colourGen = lambda : '#%02X%02X%02X' % (c_r,c_g,c_b)
        textColour = "#000000" if ((c_r * 0.299) + (c_g * 0.587) + (c_b * 0.114)) > 186 else "#FFFFFF"
        return (colourGen(),textColour)

    def _getNewColour(self,colours):
        while True:
            newColour = self._colourGen()
            if newColour not in colours:
                return newColour