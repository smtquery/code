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

def buildOrs(l):
	out = l[0]
	for c in l[1:]:
		out=f'({out} or {c})'
	return out

t_set = "*"
solvers = ["CVC5","Z3Seq","Z3Str3","CVC4","Z3Noodler","Ostrich"]
init_s_preds = {"SAT" : buildOrs([f'(isCorrect({s}) and isSAT({s}))' for s in solvers]),
				"UNSAT" : buildOrs([f'isUNSAT({s})' for s in solvers])}
c_pre = "Select LatexCactusPlot From "+t_set
s_pre = "Select Count From "+t_set

cactus = [c_pre]+[c_pre+" Where "+init_s_preds["SAT"]]+[c_pre+" Where "+init_s_preds["UNSAT"]]
selects = [s_pre+" Where "+init_s_preds["SAT"]]+[s_pre+" Where "+init_s_preds["UNSAT"]]

pre = "Select Count From "+t_set+" Where"

basis = {"WEQ" : ["hasWEQ","(not hasLinears)", "(not hasRegex)", "(not isImplicitlyUniversal)"],
		 "RE":  ["(not hasWEQ)","(not hasLinears)", "hasRegex", "(not hasFactorRelation)"],
		 "WEQ+LEN":  ["hasWEQ","hasLinears", "(not hasRegex)", "(not isImplicitlyUniversal)"],
		 "RE+LEN":  ["(not hasWEQ)","hasLinears", "hasRegex", "(not hasFactorRelation)"], 
		 "WEQ+RE":  ["hasWEQ","(not hasLinears)", "hasRegex", "(not isImplicitlyUniversal)"],
		 "WEQ+RE+LEN":  ["hasWEQ","hasLinears", "hasRegex", "(not isImplicitlyUniversal)"]
		 }

additions = { "NONE" : ["(not hasTransductions)","(not hasLexConstraints)","(not hasSubstring)","(not hasStringAt)", "(not hasIndexOf)", "(not hasStringNumberConstraints)"],    # Table 1, exclude_all
			  "SN" : ["(not hasTransductions)","(not hasLexConstraints)","(not hasSubstring)","(not hasStringAt)", "(not hasIndexOf)", "hasStringNumberConstraints"],   # Table 2, string_number
			  "R" : ["hasTransductions","(not hasLexConstraints)","(not hasSubstring)","(not hasStringAt)", "(not hasIndexOf)", "(not hasStringNumberConstraints)"],     # Table 3, replacement
			  "S" : ["(not hasTransductions)","(not hasLexConstraints)","(hasSubstring or hasStringAt)", "(not hasIndexOf)", "(not hasStringNumberConstraints)"],             # Table 4.a, substring
			   "I" : ["(not hasTransductions)","(not hasLexConstraints)","(not hasSubstring)","(not hasStringAt)", "hasIndexOf", "(not hasStringNumberConstraints)"],         # Table 4.b, indexof
			}

fragments = dict()
for (a,aa) in additions.items():
	for (f,ff) in basis.items():
		fragments[f'{f}+{a}'] = ff+aa

predicates = {k : buildAnds(fragments[k]) for k in fragments.keys()}



# Dec Frags
decidability = {"DEC"  : ["WEQ+NONE","RE+NONE","RE+LEN+NONE","RE+LEN+SN"],
				"UDEC" : ["WEQ+LEN+SN","WEQ+RE+LEN+SN","RE+LEN+SN","WEQ+R","RE+R","WEQ+LEN+R","RE+LEN+R","WEQ+RE+R","WEQ+RE+LEN+R","WEQ+LEN+I"],
				"UNK"  : ["WEQ+LEN+NONE","WEQ+RE+LEN+NONE", "WEQ+LEN+S"]				
				}

# Initial Evalution
slit_solver_preds = dict()
slit_solver_preds["SAT"] = buildAnds([f"(isSAT({s}) and isCorrect({s}))" for s in solvers])
slit_solver_preds["UNSAT"] = buildAnds([f"isUNSAT({s})" for s in solvers])
slit_solver_preds["UNKNOWN"] = buildAnds([f"isUNKNOWN({s})" for s in solvers])


s_pre = "Select LatexCactusPlot From "+t_set+" Where"
sf_queries = []
s_preds = [f"(isSAT({s}) and isCorrect({s}))" for s in solvers]+[f"isUNSAT({s})" for s in solvers]




for (k,v) in decidability.items():
    l = []
    for kk in v:
        l+=[predicates[kk]]
    predicates[k] = buildOrs(l)

    sf_queries+=[f'{s_pre} {predicates[k]}']
    #for s in s_preds:
    #   sf_queries+=[f'{pre} {buildAnds([predicates[k],s])}']



if False:
    queries = []
    for p in predicates.values():
        queries+=[f'{pre} {p}']
else:
    queries = sf_queries

#queries = [f'{pre} {q}' for q in slit_solver_preds.values()]
#queries = cactus+selects


data = []
try:
	os.makedirs(output_path)
except Exception as e:
	pass

for i,q in enumerate(queries):
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
