import smtquery.smtcon
import smtquery.smtcon.exprfun
from smtquery.intel.plugins.probes import Probes
import smtquery.ui
from smtquery.solvers.solver import *
import time
from matplotlib import pyplot as plt
import pandas as pd

class OperatorPlot: 
    output_folder = "./output/operator_plot/"   
    @staticmethod
    def getName ():
        return "OperatorPlot"

    def finalise(self,results,total,count_opertors=False,split_ops=True):
        res = [r for r in results if r != None]
        totalCount = len(res)
        if count_opertors:
            ops = self._merge_dicts(res)
        else:
            ops = self._acc_dicts(res)
        
        if split_ops:
            s_ops = self._prefix_split_ops(ops)
        else:
            s_ops = {"all" : ops}
        
        for p in s_ops.keys():
            self._plot_operations(s_ops[p],p)

        with smtquery.ui.output.makePlainMessager () as mess:
            mess.message (f"Total matching instances: {totalCount} of {total} within the selected set ({(100/total)*totalCount}%).\n")
        

    def __call__  (self,smtfile):
        intels = [smtquery.smtcon.exprfun.CountOperators]
        p = Probes()
        return p.getIntel(smtfile,intels).get_intel()[p.getIntelKey2Class(intels[0])]

    def _merge_dicts(self, data):
        d_new = self._neutral_ops()
        for d in data:
            for k in set(d_new.keys()).union(set(d.keys())):
                if k in d_new and k in d:
                    d_new[k]+=d[k]
        return d_new

    def _acc_dicts(self, data):
        d_new = self._neutral_ops()
        for d in data:
            for k in set(d_new.keys()).union(set(d.keys())):
                if k in d_new and k in d:
                    d_new[k]+=1
        return d_new

    def _plot_operations(self,ops,prefix):
        # Convert the dictionary into a DataFrame
        df = pd.DataFrame(list(ops.items()), columns=['Operation', 'Occurrences'])
        df = df.sort_values(by='Occurrences', ascending=False)
        
        # Create a bar chart
        ax = df.plot(kind='bar', x='Operation', y='Occurrences', legend=False, figsize=(10, 4),logy=True)
        ax.set_ylim(bottom=0)
        # Set the title and labels
        #ax.set_title('Occurrences of SMT-LIB QF_S Operations')
        ax.set_xlabel('Operation')
        ax.set_ylabel('Occurrences')
        
        # Rotate x-axis labels vertically
        plt.xticks(rotation=90)
        
        # Show the plot
        plt.tight_layout()  # Adjust layout to make room for the rotated x-axis labels
        os.makedirs(self.output_folder,exist_ok = True)
        plt.savefig(f"{self.output_folder}/operatorPlot_{prefix}_{int(time.time())}.pdf",format="pdf",dpi=320)

    def _neutral_ops(self):
        return {
            'str.++': 0,         # String concatenation
            'str.len': 0,        # String length
            'str.at': 0,         # Character at position
            'str.substr': 0,     # Substring
            'str.indexof': 0,    # Index of substring
            'str.contains': 0,   # Check if contains substring
            'str.prefixof': 0,   # Check if prefix
            'str.suffixof': 0,   # Check if suffix
            'str.replace': 0,    # Replace substring
            'str.replace_all': 0,    # Replace substring
            'str.replace_re': 0,    # Replace substring
            'str.replace_re_all': 0,    # Replace substring
            'str.<': 0,          # Lexicographical less than
            'str.<=': 0,         # Lexicographical less or equal
            'str.to_int': 0,     # Convert string to integer
            'str.from_int': 0,   # Convert integer to string
            'str.in_re': 0,      # String membership in regular expression
            'str.to_re': 0,      # Convert string to regular expression
            # Regular expression operators
            're.none': 0,        # The empty language
            're.all': 0,         # The language of all strings
            're.allchar': 0,     # The language of all single characters
            're.++': 0,          # Concatenation of regular expressions
            're.union': 0,       # Union of regular expressions
            're.inter': 0,       # Intersection of regular expressions
            're.*': 0,           # Kleene star (closure) of a regular expression
            're.+': 0,           # One or more repetitions of a regular expression
            're.opt': 0,         # Optional regular expression (zero or one occurrence)
            're.range': 0,       # Regular expression of a range of characters
            're.comp': 0,        # Complement of a regular expression
            're.diff': 0,        # Difference of regular expressions
            '_ re.^': 0,    # Exponentiation of a regular expression
            '_ re.loop': 0 # Looping of a regular expression
        }
    
    def _prefix_split_ops(self,ops):
        s_ops = dict()
        for op in ops.keys():
            prefix = op.split(".")[0]
            if prefix not in s_ops:
                s_ops[prefix] = dict()
            s_ops[prefix][op] = ops[op]
        return s_ops

def PullExtractor():
    return [OperatorPlot]
