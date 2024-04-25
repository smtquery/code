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

# initial setup
t_set = "pisa"
solvers = ["CVC5","Z3Seq","Z3Str3","CVC4","Z3Noodler","Ostrich"]
cactus_pre = "Select LatexCactusPlot From "+t_set
count_pre = "Select Count From "+t_set
features_pre = "Select Features From"
dt_pre = "Select DecisionTree From"

# Initial Evalution / SAT+UNSAT instances
init_s_preds = {"SAT" : buildOrs([f'(isCorrect({s}) and isSAT({s}))' for s in solvers]),
				"UNSAT" : "("+buildOrs([f'isUNSAT({s})' for s in solvers])+" and (not "+buildOrs([f'(isCorrect({s}) and isSAT({s}))' for s in solvers])+"))" }


# Build fragments
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

# Features
bench_folder = "./data/smtfiles"

### BUILD Queries
queries = []

# Figure 6 and counts
queries+=[cactus_pre]+[cactus_pre+" Where "+init_s_preds["SAT"]]+[cactus_pre+" Where "+init_s_preds["UNSAT"]]  # Plots
queries+=[count_pre+" Where "+init_s_preds["SAT"]]+[count_pre+" Where "+init_s_preds["UNSAT"]]                 # Counting

# Figure 7
queries+=["Select OperatorPlot From "+t_set]

# Fragments -- Section 3.3 
for p in predicates.values():
	queries+=[f'{count_pre} Where {p}']

# Decidability -- Section 3.3 
for (k,v) in decidability.items():
	predicates[k] = buildOrs([predicates[kk] for kk in v])
	queries+=[f'{count_pre} Where {predicates[k]}']            # Counting
	queries+=[f'{cactus_pre} Where {predicates[k]}']            # Plots

# Features
queries+=[f'{features_pre} {o}' for o in os.listdir(bench_folder) if os.path.isdir(os.path.join(bench_folder,o))]+[f'{dt_pre} {o}' for o in os.listdir(bench_folder) if os.path.isdir(os.path.join(bench_folder,o))]

queries=[f'{dt_pre} {o}' for o in os.listdir(bench_folder) if os.path.isdir(os.path.join(bench_folder,o))]

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
