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

def make_new_condition(old_cond, file, b_varsat, varsat):
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

if __name__ == "__main__":
    arg = sys.argv[1]
    pick_file = sys.argv[2] if len(sys.argv) > 2 else "rejected.bin"
    pick_handle = open(pick_file, 'rb')
    rej_strs = pickle.load(pick_handle)

    # Get base values from the non-crashing run with the longest input
    basein = ""
    for cand in rej_strs:
        print(cand)
        basein = cand[1] if len(cand[1]) > len(basein) else basein

    (_, b_clines, b_vrs) = argtracer.trace(arg, basein)

    # Mutation guided by rejected strings
    s = rej_strs[0][0]

    (lines, clines, vrs) = argtracer.trace(arg, s)

    delta = get_diff(b_clines, clines)

    print("______________")
    print("Executed conditions:", b_clines)
    print("Available variables", b_vrs)
    print("______________")
    print("Used string:", repr(s))
    print("Executed lines:", lines)
    print("Executed conditions:", clines)
    print("Available strings:", vrs)
    print("Difference to base:", delta)
    print("")
    if (was_manually_raised(arg, lines[0])):
        for fix in make_new_condition(delta[0], arg, b_vrs, vrs):
            print("Possible fix:", fix)
    else:
        print("Mutation complete.")
