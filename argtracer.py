#!/usr/bin/env python3
import imp
import sys
import traceback
import taintedstr
import re
import functools

clines = []
lines = []
vrs = {}
ar = ""

RE_if = re.compile(r'^\s*(if|elif)\s+([^:]|(:[^\s]))+:\s.*')

@functools.lru_cache(maxsize=None)
def get_code_from_file(arg, linenum):
    with open(arg) as fp:
        for i, line in enumerate(fp):
            if i+1 == linenum:
                return line

@functools.lru_cache(maxsize=None)            
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

def line_tracer(frame, event, arg):
    if event == 'line':
        global lines
        global clines
        global fl
        global ar
        if fl in frame.f_code.co_filename:
            lines.insert(0, frame.f_lineno)
            res = get_code_from_file(ar, frame.f_lineno)
            if res and RE_if.match(res):
                cond = extract_from_condition(res)
                bval = eval(cond, frame.f_globals, frame.f_locals)
                clines.insert(0, (frame.f_lineno, bval))
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
    global ar
    ar = arg
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
    return (lines, clines, vrs)