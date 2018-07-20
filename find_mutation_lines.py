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

def get_diff(lst1, lst2):
    diff = []
    if len(lst1) >= len(lst2):
        l1 = lst1
        l2 = lst2
    else:
        l1 = lst2
        l2 = lst1
    for e in l1:
        if e not in l2:
            diff.append(e)
    return diff

def make_new_conditions(old_cond, file, b_varsat, varsat):
    (lineno, state) = old_cond
    full_str = get_code_from_file(file, lineno)
    cond_str = extract_from_condition(full_str)
    valid_cond = random.choice(varsat[lineno][1]) if varsat[lineno] else None
    if not valid_cond:
        choices = list(set(b_varsat[lineno]).intersect(set(varsat[lineno])))
        valid_cond = random.choice(choices)
        if not valid_cond:
            return None
    if state:
        # Falsify the condition
        valid_cond = valid_cond[0] + " != \"" + valid_cond[1] + "\""
        new_cond = "(" + cond_str + ") and " + valid_cond
    else:
        # Satisfy the condition
        valid_cond = valid_cond[0] + " == \"" + valid_cond[1] + "\""
        new_cond = "(" + cond_str + ") or " + valid_cond
    return (full_str.replace(cond_str, new_cond), full_str.replace(cond_str, valid_cond))

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

    (_, b_clines, b_vrs, _) = argtracer.trace(arg, basein)

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

            (lines, clines, vrs, err) = argtracer.trace(arg, s)

            delta = get_diff(b_clines, clines) if not berr else []

            print("Used string:", repr(s))
            print("Executed conditions:", clines)
            print("Difference to base:", delta)
            print("Final line:", str(lines[0]))
            print("")
            cand = mut_dir + script_name + "_" + str(str_cnt) + "_" + str(mut_cnt) + ".py"
            if not berr and err and (was_manually_raised(arg, lines[0])):
                for fix in make_new_conditions(delta[0], arg, b_vrs, vrs):
                    mods = {
                        lines[0] : fix
                        }
                    queue.append(cand)
                    file_copy_replace(cand, arg, mods)
                    mut_cnt += 1
            else:
                print("Exception manually raised:", was_manually_raised(arg, lines[0]))
                completed.append(arg)
                print("Mutation complete:", cand)
        str_cnt += 1
        print()
    cleanup(mut_dir, completed)
    print("Done. The final mutants are in:", mut_dir)
    
