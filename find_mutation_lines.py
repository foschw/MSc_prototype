#!/usr/bin/env python3
import sys
sys.path.append('.')
import taintedstr
import pickle
import re
import argtracer
import functools
from argtracer import get_code_from_file, extract_from_condition
import random
import os
import glob
import imp

RE_raise = re.compile(r'(^|\s+)raise\s+')

@functools.lru_cache(maxsize=None)
def was_manually_raised(file, lineno):
    return True if RE_raise.search(get_code_from_file(file, lineno)) else False

def get_left_diff(l1, l2):
    prim = []
    sec = []
    lns = [i[0] for i in l2]
    for e in l1:
        if e not in l2 and e not in prim and e not in sec:
            if e[0] in lns:
                prim.append(e)
            else:
                sec.append(e)
            
    return (prim, sec)

def make_new_conditions(old_cond, file, b_varsat, varsat):
    (lineno, state) = old_cond
    full_str = get_code_from_file(file, lineno)
    cond_str = extract_from_condition(full_str)
    # Conditions that hold for the last execution of the line and not for the baseline run
    easy_sat = [i for i in varsat[lineno][1] if i not in b_varsat[lineno]] if b_varsat.get(lineno) else varsat[lineno][1]
    valid_cond = random.choice(easy_sat) if easy_sat else None
    if not valid_cond:
        # Conditions that hold for all iterations over the line
        choices = [i for i in varsat[lineno][0] if i not in b_varsat[lineno]] if b_varsat.get(lineno) else None
        if choices: valid_cond = random.choice(choices)
        else:
        # Conditions that *always* hold for the given line
            choices = [i for i in varsat[lineno][0] + varsat[lineno][1]]
            valid_cond = random.choice(choices)
    if state:
        # Falsify the condition
        valid_cond = valid_cond[0] + " != \"" + valid_cond[1] + "\""
        new_cond = "(" + cond_str + ") and " + valid_cond
    else:
        # Satisfy the condition
        valid_cond = valid_cond[0] + " == \"" + valid_cond[1] + "\""
        new_cond = "(" + cond_str + ") or " + valid_cond
    return (full_str.replace(cond_str, new_cond), full_str.replace(cond_str, valid_cond))

def get_possible_fixes(delta, file, b_varsat, varsat):
    (prim, sec) = delta
    fixmap = []
    if prim:
        for (lineno, state) in prim:
            fixmap.append((lineno, make_new_conditions((lineno,state),file,b_varsat,varsat)))
    elif sec:
        for (lineno, state) in sec:
            fixmap.append((lineno, make_new_conditions((lineno,state),file,b_varsat,varsat)))
    return fixmap

def file_copy_replace(target, source, modifications):
    with open(target, "w", encoding="UTF-8") as trgt:
        with open(source, "r", encoding="UTF-8") as src:
            for i, line in enumerate(src):
                if modifications.get(i+1):
                    trgt.write(modifications[i+1])
                else:
                    trgt.write(line)

def cleanup(mut_dir, completed):
    for fl in glob.glob(mut_dir + "/*.py"):
        fl = fl.replace("\\", "/")
        if fl not in completed:
            os.remove(fl)

if __name__ == "__main__":
    arg = sys.argv[1]
    arg = arg.replace("\\", "/")
    ar1 = arg
    mut_dir = arg[arg.rfind("/")+1:arg.rfind(".")] if arg.rfind("/") >= 0 else arg[:arg.rfind(".")]
    script_name = mut_dir
    mut_dir = "mutants/" + mut_dir + "/"
    # Timeout since our modifications may cause infinite loops
    timeout = 5
    if not os.path.exists(mut_dir):
        os.makedirs(mut_dir)
    else:
        cleanup(mut_dir, [])

    # Index of the string currently processed
    str_cnt = 0
    # Mutation counter
    mut_cnt = 0
    pick_file = sys.argv[2] if len(sys.argv) > 2 else "rejected.bin"
    pick_handle = open(pick_file, 'rb')
    rej_strs = pickle.load(pick_handle)

    # Get base values from the non-crashing run with the longest input
    basein = ""
    for cand in rej_strs:
        basein = cand[1] if len(cand[1]) > len(basein) else basein

    try:
        (_, b_clines, b_vrs, _) = argtracer.trace(arg, basein, timeout=timeout)
    except Timeout:
        print("Execution timed out on basestring! Try increasing timeout (", timeout,")")

    print("Used baseinput:", repr(basein))
    completed = []

    for s in rej_strs:
        s = s[0]
        queue = [ar1]
        while queue:
            arg = queue.pop(0)
            berr = False
            # Check whether the chosen correct string is now rejected
            try:
                _mod = imp.load_source('mymod', arg)
            except:
                print("Discarded script:", arg)
                continue
            try:
                _mod.main(basein)
            except:
                berr = True
            # Mutation guided by rejected strings

            try:
                (lines, clines, vrs, err) = argtracer.trace(arg, s, timeout=timeout)
            except Timeout:
                continue

            (prim, sec) = get_left_diff(clines, b_clines) if not berr else ([],[])

            print("Current script:", arg)
            print("Used string:", repr(s))
            print("Difference to base (flipped):", prim)
            print("Difference to base (new):", sec)
            print("Final line:", str(lines[0]))
            print("")
            if not berr and err and (was_manually_raised(arg, lines[0])):
                for (linenum, fixes) in get_possible_fixes((prim, sec), arg, b_vrs, vrs):
                    for fix in fixes:
                        cand = mut_dir + script_name + "_" + str(str_cnt) + "_" + str(mut_cnt) + ".py"
                        mods = {
                            linenum : fix
                            }
                        queue.append(cand)
                        file_copy_replace(cand, arg, mods)
                        mut_cnt += 1
            else:
                print("Base rejected:", berr, ", manual:", was_manually_raised(arg, lines[0]))
                if arg not in completed: completed.append(arg)
                print("Mutation complete:", arg)
        str_cnt += 1
        print()
    cleanup(mut_dir, completed)
    print("Done. The final mutants are in:", mut_dir)
    
