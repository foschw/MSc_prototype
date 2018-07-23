#!/usr/bin/env python3
import imp
import sys
import traceback
import taintedstr
import re
import functools
from timeit import default_timer as timer

cond_dict = {}
lines = []
vrs = {}
ar = ""
timeo = None
time_start = None
# target_type = type("")
# By using the commented line instead we get a seizable improvement in execution time but may consume more memory
target_type = type(taintedstr.tstr(''))

RE_if = re.compile(r'^\s*(if|elif)\s+([^:]|(:[^\s]))+:\s.*')

class Timeout(Exception):
    pass

@functools.lru_cache(maxsize=None)
def get_code_from_file(arg, linenum):
    with open(arg, "r", encoding="UTF-8") as fp:
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
        global fl
        global ar
        global timeo
        global time_start
        global cond_dict
        global target_type
        if fl in frame.f_code.co_filename:
            if timeo:
                end = timer()
                if (end - time_start) >= timeo:
                    raise Timeout("Execution timed out!")
            lines.insert(0, frame.f_lineno)
            res = get_code_from_file(ar, frame.f_lineno)
            if res and RE_if.match(res):
                cond = extract_from_condition(res)
                try:
                    bval = eval(cond, frame.f_globals, frame.f_locals)
                    if cond_dict.get(frame.f_lineno):
                        cond_dict[frame.f_lineno].add(bval)
                    else:
                        cond_set = set()
                        cond_set.add(bval)
                        cond_dict[frame.f_lineno] = cond_set
                except:
                    # This is not a good idea, but better than crashing for now
                    print("Warning: unable to infer condition result in line:", frame.f_lineno)
                    pass
                global vrs
                vass = vrs.get(frame.f_lineno) if vrs.get(frame.f_lineno) else []
                avail = [v for v in vass[0]] if vass else None
                for var in frame.f_locals.keys():
                    val = frame.f_locals[var]
                    if type(val) == target_type:
                        if not avail or var in avail and (var,val) not in vass:
                            vass.append((var, str(val)))
                vrs[frame.f_lineno] = vass

    return line_tracer

def trace(arg, inpt, timeout=None):
    global lines
    global vrs
    global ar
    global timeo
    global time_start
    global cond_dict
    if timeout:
        time_start = timer()
        timeo = timeout
    else:
        timeo = None
        time_start = None
    ar = arg
    clines = []
    lines = []
    vrs = {}
    err = False
    # Modify this case if you want to use a different type here (e.g. when using str)
    inpt = taintedstr.tstr(inpt)
    _mod = imp.load_source('mymod', arg)
    global fl
    fl = arg.replace("\\", "/")
    fl = arg[arg.index("/"):] if arg.startswith(".") else arg
    fl = fl[:arg.rindex("/")-1] if arg.rfind("/") != -1 else fl
    try:
        sys.settrace(line_tracer)
        res = _mod.main(inpt)
    except Timeout:
        sys.settrace(None)
        raise
    except:
        sys.settrace(None)
        traceback.print_exc()
        err = True
    sys.settrace(None)
    for lne in cond_dict.keys():
        bval = cond_dict[lne]
        if len(bval) == 1:
            clines.append((lne, cond_dict[lne].pop()))
    return (lines.copy(), clines, vrs.copy(), err)
