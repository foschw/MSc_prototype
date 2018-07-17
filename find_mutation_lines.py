#!/usr/bin/env python3
import sys
sys.path.append('.')
import taintedstr
import pickle
import re
import ArgTracer

RE_if = re.compile(r'^\s*(if|elif)\s+([^:]|(:[^\s]))+:\s.*')

def extract_from_condition(cond):
    poss = cond.count(":")
    if poss < 1:
        raise ValueError(cond, "is is not a valid condition statement!")
    elif poss == 1:
        try:
            eval(cond[cond.find("if")+2:cond.find(":")])
        except SyntaxError:
            raise ValueError(cond, "is not executable in python")
        except:
            return cond[cond.find("if")+2:cond.find(":")]
    else:
        idx = 0
        lastvalid = ""
        while poss > 0:
            idx = cond.find(":", idx+1)
            poss -= 1
            substr = cond[cond.find("if")+2:idx]
            try:
                eval(substr)
            except SyntaxError:
                continue
            except:
                lastvalid = substr
        return lastvalid

if __name__ == "__main__":
    arg = sys.argv[1]
    pick_file = sys.argv[2] if len(sys.argv) > 2 else "rejected.bin"
    pick_handle = open(pick_file, 'rb')
    (rej_strs, errs) = pickle.load(pick_handle)
   
    s = rej_strs[0]
    
    (lines, vrs) = ArgTracer.trace(arg, s)

    print(lines)
    print(s)
    print(vrs)

    options = {}

    with open(arg) as fp:
        for i, line in enumerate(fp):
            if i+1 in lines and (RE_if.findall(line)):
                options[i+1] = (line, 2)
                print(extract_from_condition(line))

    print(options)
