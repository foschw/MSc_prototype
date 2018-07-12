#!/usr/bin/env python3
import sys
sys.path.append('.')
import imp
import taintedstr
import pickle

lines_raw = []

def line_tracer(frame, event, arg):
    if event == 'line':
        global lines_raw
        lines_raw.append((frame.f_code.co_filename, frame.f_lineno))

    return line_tracer

if __name__ == "__main__":
    arg = sys.argv[1]
    _mod = imp.load_source('mymod', arg)
    pick_file = sys.argv[2] if len(sys.argv) > 2 else "rejected.bin"
    pick_handle = open(pick_file, 'rb')
    rej_strs = pickle.load(pick_handle)
    s = rej_strs.pop()
    try:
        sys.settrace(line_tracer)
        res = _mod.main(s)
    except:
        sys.settrace(None)
    else:
        assert(False)
    sys.settrace(None)
    lines = []
    
    fl = arg.replace("\\", "/")
    fl = arg[arg.index("/"):] if arg.startswith(".") else arg
    for (file, line) in lines_raw:
        if fl in file:
            if line in lines:
                lines.remove(line)
            lines.insert(0, line)

    print(lines)
