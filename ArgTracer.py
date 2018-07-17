#!/usr/bin/env python3
import imp
import sys
import traceback
import taintedstr

lines = []
vrs = {}

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

def trace(arg, inpt):
    global lines
    global vrs
    lines = []
    vrs = {}
    _mod = imp.load_source('mymod', arg)
    global fl
    fl = arg.replace("\\", "/")
    fl = arg[arg.index("/"):] if arg.startswith(".") else arg
    fl = fl[:arg.rindex("/")-1] if arg.rfind("/") != -1 else fl
    try:
        sys.settrace(line_tracer)
        res = _mod.main(inpt)
    except:
        sys.settrace(None)
        traceback.print_exc()
    else:
        assert(False)
    sys.settrace(None)
    return (lines, vrs)
