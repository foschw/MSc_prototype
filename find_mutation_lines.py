#!/usr/bin/env python3
import sys
sys.path.append('.')
import imp
import taintedstr
import pickle

lines = []
vrs = {}

def line_tracer(frame, event, arg):
    if event == 'line':
        global lines
        global fl
        if fl in frame.f_code.co_filename:
            lines.append(frame.f_lineno)
            global vrs
            vass = vrs.get(frame.f_lineno) if vrs.get(frame.f_lineno) else []
            for var in frame.f_locals.keys():
                val = frame.f_locals[var]
                if type(val) == type(taintedstr.tstr('')):
                    vass.append((var, val))
            vrs[frame.f_lineno] = vass

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
    s = rej_strs.pop()
    try:
        sys.settrace(line_tracer)
        res = _mod.main(s)
    except:
        sys.settrace(None)
    else:
        assert(False)
    sys.settrace(None)

    print(lines)
    print(s)
    print(vrs)
