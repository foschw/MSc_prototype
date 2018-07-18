#!/usr/bin/env python3
import sys
sys.path.append('.')
import taintedstr
import pickle
import re
import argtracer

RE_if = re.compile(r'^\s*(if|elif)\s+([^:]|(:[^\s]))+:\s.*')

def extract_from_condition(cond):
    poss = cond.count(":")
    if poss < 1:
        return ""
    elif poss == 1:
        try:
            eval(cond[cond.find("if")+2:cond.find(":")])
        except SyntaxError:
            return ""
        except:
            pass
        return cond[cond.find("if")+2:cond.find(":")].lstrip()
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
                pass
            lastvalid = substr
        return lastvalid.lstrip()

if __name__ == "__main__":
    arg = sys.argv[1]
    pick_file = sys.argv[2] if len(sys.argv) > 2 else "rejected.bin"
    pick_handle = open(pick_file, 'rb')
    (rej_strs, errs) = pickle.load(pick_handle)
   
    s = rej_strs[0]

    (lines, clines, vrs) = argtracer.trace(arg, s)
    
    print("Used string:", repr(s))
    print("Executed lines:", lines)
    print("Executed conditions:", clines)
    print("Available strings:", vrs)
