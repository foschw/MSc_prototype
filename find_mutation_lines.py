#!/usr/bin/env python3
import sys
sys.path.append('.')
import imp
import taintedstr
import pickle
import traceback
import re

lines = []
vrs = {}
RE_if = re.compile(r'^\s*(if|elif)\s+([^:]|(:[^\s]))+:\s.*')
RE_cond = re.compile(r'^\s*(if|elif)\s+([^:]|(:[^\s]))+:\s')

def line_tracer(frame, event, arg):
    if event == 'line':
        global lines
        global fl
        if fl in frame.f_code.co_filename:
            lines.insert(0, frame.f_lineno)
            global vrs
            vass = vrs.get(frame.f_lineno)[0] if vrs.get(frame.f_lineno) else []
            vass_curr = []
            for var in frame.f_locals.keys():
                val = frame.f_locals[var]
                if type(val) == type(taintedstr.tstr('')):
                    if (var,val) not in vass:                    
                        vass_curr.append((var,val))
                    vass.append((var, val))
            vrs[frame.f_lineno] = (vass, vass_curr)

    return line_tracer

if __name__ == "__main__":
    arg = sys.argv[1]
    _mod = imp.load_source('mymod', arg)
    pick_file = sys.argv[2] if len(sys.argv) > 2 else "rejected.bin"
    pick_handle = open(pick_file, 'rb')
    (rej_strs, errs) = pickle.load(pick_handle)
    global fl
    fl = arg.replace("\\", "/")
    fl = arg[arg.index("/"):] if arg.startswith(".") else arg
    fl = fl[:arg.rindex("/")-1] if arg.rfind("/") != -1 else fl
    s = rej_strs[0]
    try:
        sys.settrace(line_tracer)
        res = _mod.main(s)
    except:
        sys.settrace(None)
        traceback.print_exc()
    else:
        assert(False)
    sys.settrace(None)

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
