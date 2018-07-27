#!/usr/bin/env python3
import sys
sys.path.append('.')
import taintedstr
import pickle
import re
import argtracer
from argtracer import Timeout as Timeout
import random
import os
import glob
import imp

def get_left_diff(d1, d2):
    prim = []
    sec = []
    for e in d1.keys():
        s1 = d1[e]
        s2 = d2.get(e)
        if s2:
            if len(s1) == 2 and len(s2) == 1:
                prim.append((e, s1.difference(s2).pop()))
            elif len(s1) == 1 and len(s2) == 1 and len(s1.intersection(s2)) == 0:
                prim.append((e, s1.pop()))
                
        elif len(s1) == 1:
            sec.append((e,s1.pop()))

    return (prim, sec)

def sanitize(valuestring):
    return repr(valuestring)

def make_new_conditions(old_cond, file, b_varsat, varsat):
    global manual_errs
    (lineno, state) = old_cond
    (full_str, startline, endline, offset) = manual_errs.get_if_and_range_for_line(lineno, file)
    cond_str = manual_errs.get_condition_from_line(lineno, file)
    # Conditions that hold for the last execution of the line and not for the baseline run
    lcand = varsat.get(lineno) if varsat.get(lineno) else None
    if lcand:
        rcand = b_varsat[lineno] if b_varsat.get(lineno) else []
    else: return []

    choices = [i for i in lcand if i not in rcand]
    stable = {}
    for i in choices:
        stable[i[0]] = i[1] if not stable.get(i[0]) or stable.get(i[0]) == i[1] else -1
    stable = [i for i in choices if type(stable[i[0]]) != type(1)]
    print("Possible choices:", choices)
    print("Stable choices:", stable)
    if stable or choices:
    	valid_cond = random.choice(stable) if stable else random.choice(choices)
    else:
    	return []
    if state:
        # Falsify the condition
        valid_cond = valid_cond[0] + " != " + sanitize(valid_cond[1])
        new_cond = "(" + cond_str + ") and " + valid_cond
    else:
        # Satisfy the condition
        valid_cond = valid_cond[0] + " == " + sanitize(valid_cond[1])
        new_cond = "(" + cond_str + ") or " + valid_cond
    
    nc1 = full_str[:offset] + new_cond + full_str[offset+len(cond_str):]
    nc2 = full_str[:offset].rstrip() + " " + valid_cond + ":"
    for i in range(endline-startline-1):
    	nc2 = nc2 + "\n"
    nc2 = nc2 + full_str[offset+len(cond_str)+1:]
    return ((str(nc1), str(nc2)), startline, endline)

def get_possible_fixes(delta, file, b_varsat, varsat):
    (prim, sec) = delta
    fixmap = []
    if prim:
        for (lineno, state) in prim:
            ((cand1, cand2), startline, endline) = make_new_conditions((lineno,state),file,b_varsat,varsat)
            if cand1 and cand2: fixmap.append(([cand1, cand2],startline, endline))
    elif sec:
        for (lineno, state) in sec:
            ((cand1, cand2), startline, endline) = make_new_conditions((lineno,state),file,b_varsat,varsat)
            if cand1 and cand2: fixmap.append(([cand1, cand2],startline, endline))
    return fixmap

def file_copy_replace(target, source, modifications):
    with open(target, "w", encoding="UTF-8") as trgt:
        with open(source, "r", encoding="UTF-8") as src:
            for i, line in enumerate(src):
                if modifications.get(i+1) is not None and modifications.get(i+1) != "":
                    trgt.write(modifications[i+1])
                elif modifications.get(i+1) != "":
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
    # Store the reason why the mutantion was completed
    mutants_with_cause = []
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

    # Precompute the locations of manually raised errors
    global manual_errs
    manual_errs = argtracer.compute_base_ast(ar1)

    # Get base values from the non-crashing run with the longest input
    basein = ""
    for cand in rej_strs:
        basein = cand[1] if len(cand[1]) > len(basein) else basein
    try:
        (_, b_cdict, b_vrs, _) = argtracer.trace(arg, basein, timeout=timeout)
    except Timeout:
        print("Execution timed out on basestring! Try increasing timeout (currently", timeout," seconds)")

    print("Used baseinput:", repr(basein))

    for s in rej_strs:
        s = s[0]
        queue = [(ar1, [])]
        discarded = set()
        while queue:
            (arg, history) = queue.pop(0)
            print("Current script:", arg)
            # Check whether the chosen correct string is now rejected
            try:
                _mod = imp.load_source('mymod', arg)
            except:
                print("Discarded script:", arg, "(import error)")
                discarded.add(arg)
                continue
            print("Executing basestring...")
            try:
                (_, _, _, berr) = argtracer.trace(arg, basein, timeout=timeout)
            except argtracer.Timeout:
                print("Discarding,", arg, "(basestring timed out)")
                discarded.add(arg)
                continue

            # Mutation guided by rejected strings

            try:
                (lines, cdict, vrs, err) = argtracer.trace(arg, s, timeout=timeout)
            except:
            	print("Tracer timed out on mutated string")
            	discarded.add(arg)
            	continue
            # Moved this condition after the second call to make missing infinite loops less likely
            if berr:
                print("Mutation complete:", arg, "(base rejected)")
                mutants_with_cause.append((arg, "valid string rejected"))
                continue

            (prim, sec) = get_left_diff(cdict, b_cdict) if not berr else ([],[])
            prim = [e for e in prim if e[0] not in history]
            sec = [e for e in sec if e[0] not in history]
            print("Used string:", repr(s))
            print("Difference to base (flipped):", prim)
            print("Difference to base (new):", sec)
            print("Final line:", str(lines[0]))
            print("")
            print("Change history:", history)
            if err:
            	# Check whether the exception is user-defined (then it has to be manually raised) or whether the last executed line contained a raise expression
            	manual = hasattr(err,"__module__") or manual_errs.is_exception_line(lines[0])
            	err = True
            print("Mutated string rejected:", err, "manually raised:", manual)
            if err and manual:
                discarded.add(arg)
                for fix_element in get_possible_fixes((prim, sec), arg, b_vrs, vrs):
                    (fix_lst, startline, endline) = fix_element
                    for fix in fix_lst:
                        cand = mut_dir + script_name + "_" + str(str_cnt) + "_" + str(mut_cnt) + ".py"
                        mods = {}
                        mods[startline] = fix
                        for intermed_line in range(startline+1, endline+1):
                        	mods[intermed_line] = ""
                        queue.append((cand, history.copy()+[startline]))
                        file_copy_replace(cand, arg, mods)
                        mut_cnt += 1
            else:
            	print("Mutation complete:", arg, "(mutated string accepted)")
            	if arg != ar1:
            		mutants_with_cause.append((arg, "mutated string accepted"))
            		
        discarded.discard(ar1)
        for scrpt in discarded:
            print("Removed:", scrpt)
            os.remove(scrpt)
        str_cnt += 1
        mut_cnt = 0
        print("Processing string number:", str(str_cnt), "/", str(len(rej_strs)))
    print("Done. The final mutants are in:", mut_dir)
    with open(mut_dir[:-1] + "_inputs.log", "w", encoding="UTF-8") as file:
            for i in range(len(rej_strs)):
                file.write(str(i) + ": " + repr(rej_strs[i][0])+"\n")
            file.write("The baseinput was:" + repr(basein))

    with open(mut_dir[:-1] + ".log", "w", encoding="UTF-8") as file:
    	for e in mutants_with_cause:
    		file.write(repr(e) + "\n")
