#!/usr/bin/env python3
import sys
sys.path.append('.')
import imp
import taintedstr
import pickle
import traceback
import re
import ArgTracer

RE_if = re.compile(r'^\s*(if|elif)\s+([^:]|(:[^\s]))+:\s.*')
RE_cond = re.compile(r'^\s*(if|elif)\s+([^:]|(:[^\s]))+:\s')

if __name__ == "__main__":
    arg = sys.argv[1]
    _mod = imp.load_source('mymod', arg)
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
                print(RE_cond.match(line).group())

    print(options)
