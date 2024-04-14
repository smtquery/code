import time
from subprocess import run, PIPE
import tabulate
import os

smtquery_exe = "bin/smtquery"
output_path = "smpl_out"
def runner(q,param):
	try:
		t_start = time.time()  
		p = run(["python3",smtquery_exe,param], stdout=PIPE, input=q, encoding='ascii')
		t_end = time.time() - t_start #seconds
		return (t_end,str(p).split('Waiting for results ...\\n')[1])
	except:
		return None

def buildAnds(l):
	out = l[0]
	for c in l[1:]:
		out=f'({out} and {c})'
	return out

t_set = "*"

cactus = ["Select LatexCactusPlot From *",
        "Select LatexCactusPlot From * Where (((isCorrect(CVC5) and isSAT(CVC5)) or (isCorrect(Z3Str3) and isSAT(Z3Str3))) or (isCorrect(Z3Seq) and isSAT(Z3Seq)))",
        "Select LatexCactusPlot From * Where ((isUNSAT(CVC5) or isUNSAT(Z3Str3)) or isUNSAT(Z3Seq))"]


pre = "Select Count From "+t_set+" Where "
basis = ["(hasWEQ and ((not hasLinears) and (not hasRegex)))",
		"(hasRegex and (((not hasLinears) and (not hasRegex)) and (not hasFactorRelation)))",
		"(hasWEQ and (hasLinears and (not hasRegex)))",
		"(hasWEQ and ((not hasLinears) and hasRegex))",
		"(hasRegex and ((hasLinears and (not hasRegex)) and (not hasFactorRelation)))",
		"(hasWEQ and (hasLinears and hasRegex))"]

first = [f'{pre}({b} and (not hasHOL))' for b in basis]

l = ["(not hasTransductions)","(not hasLexConstraints)","(not hasSubstring)","(not hasStringAt)", "(not hasIndexOf)", "hasStringNumberConstraints"]
second = [f'{pre}({b} and {buildAnds(l)})' for b in basis]

l = ["hasTransductions","(not hasLexConstraints)","(not hasSubstring)","(not hasStringAt)", "(not hasIndexOf)", "(not hasStringNumberConstraints)"]
third = [f'{pre}({b} and {buildAnds(l)})' for b in basis]

l = ["(not hasTransductions)","(not hasLexConstraints)","(not hasSubstring)","hasStringAt", "hasIndexOf", "(not hasStringNumberConstraints)"]
fourth = [f'{pre}({b} and {buildAnds(l)})' for b in basis]


querys = cactus+first+second+third+fourth

data = []
try:
	os.makedirs(output_path)
except Exception as e:
	pass

for i,q in enumerate(querys):
    print(f"processing {q}")
    t = runner(q,'qlang')
    f_name = f"{output_path}/output_{i}_{int(time.time())}.txt"
    if t != None:
        with open(f'{f_name}', 'w') as f:
            f.write(q)
            f.write(t[1].replace("\\x1b[0J","").replace("\\n","\n"))
        data+=[(i,q,t[0],f_name)]
    else:
        data+=[(i,q,None,f_name)]
	


print(tabulate.tabulate(data,headers=["Query #","Query","Runtime","Output File"]))
