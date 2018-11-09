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

# Computes the "left difference" of two sets.
# This returns two sets: 
# prim(ary): the list of conditions that have a fixed value for the valid string which differs from the mutated string
# sec(ondary): the list of condition that the mutated string caused but were not relevant to the original string (either True and False or not seen at all).
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

# Sanitizes an input string. Introduced for ease of modification.
def sanitize(valuestring):
    return repr(valuestring)

# Creates all possible conditions that may adjust the path of the mutated string to be like the original string
# Parameters:
# old_cond: The pair (old condition line number, truth value)
# file: The current mutants file path
# b_varsat: The variable assignments of the original string (base string)
# varsat: The variable assignments encountered for the mutated string
def make_new_conditions(old_cond, file, b_varsat, varsat):
    global manual_errs
    (lineno, state) = old_cond
    # Get the full condition string
    full_str = manual_errs.get_if_from_line(lineno, file)
    # Reduce the string to only the condition, i.e. "if True:" becomes "True"
    cond_str = full_str[full_str.find("if")+3:full_str.rfind(":")]
    # Conditions that hold for the last execution of the line and not for the baseline run
    lcand = varsat.get(lineno) if varsat.get(lineno) else None
    if lcand:
        rcand = b_varsat[lineno] if b_varsat.get(lineno) else []
    else: return []

    choices = [i for i in lcand if i not in rcand]
    print("Possible choices:", choices)
    if not choices:
        return []

    possible_conditions = []
    # Generate all conditions that may flip the truth value
    for valid_cond in choices:
        if state:
            # Falsify the condition
            valid_cond = valid_cond[0] + " != " + sanitize(valid_cond[1])
            new_cond = "(" + cond_str.lstrip() + ") and " + valid_cond
        else:
            # Satisfy the condition
            valid_cond = valid_cond[0] + " == " + sanitize(valid_cond[1])
            new_cond = "(" + cond_str.lstrip() + ") or " + valid_cond
        
        nc1 = full_str[:full_str.find("if")+2] + " " + new_cond + ":"
        nc2 = full_str[:full_str.find("if")+2] + " " + valid_cond + ":"
        possible_conditions.append(str(nc1))
        possible_conditions.append(str(nc2))

    return possible_conditions

# Generate all possible new conditions from a delta (pair of primary and secondary condition differences).
def get_possible_fixes(delta, file, b_varsat, varsat):
    (prim, sec) = delta
    fixmap = []
    # In case there are primary candidates generate a mutant for all of them.
    if prim:
        for (lineno, state) in prim:
        	fix_list = make_new_conditions((lineno,state),file,b_varsat,varsat)
        	if fix_list:
        	    fixmap.append((fix_list, lineno))
    # Otherwise test all remaining candidates
    elif sec:
        for (lineno, state) in sec:
        	fix_list = make_new_conditions((lineno,state),file,b_varsat,varsat)
        	if fix_list:
        	    fixmap.append((fix_list, lineno))
    # Returns a list of ([possible fixes for a line], line number)
    return fixmap

# Creates a mutant by copying the script it is derived from and applying modifications for given lines
def file_copy_replace(target, source, modifications):
    with open(target, "w", encoding="UTF-8") as trgt:
        with open(source, "r", encoding="UTF-8") as src:
            for i, line in enumerate(src):
                if modifications.get(i+1) is not None and modifications.get(i+1) != "":
                    trgt.write(modifications[i+1])
                elif modifications.get(i+1) != "":
                    trgt.write(line)

# Removes all mutants that are intermediate (i.e. we cannot tell whether they are equivalent)
# The argument completed stores all non-equivalent mutants
def cleanup(mut_dir, completed):
    for fl in glob.glob(mut_dir + "/*.py"):
        fl = fl.replace("\\", "/")
        if fl not in completed:
            os.remove(fl)

def main(argv):
    arg = argv[1]
    arg = arg.replace("\\", "/")
    ar1 = arg
    orig_file = ar1
    mut_dir = arg[arg.rfind("/")+1:arg.rfind(".")] if arg.rfind("/") >= 0 else arg[:arg.rfind(".")]
    script_name = mut_dir
    mut_dir = "mutants/" + mut_dir + "/"
    # Store the reason why the mutation was completed
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
    pick_file = argv[2] if len(argv) > 2 else "rejected.bin"
    pick_handle = open(pick_file, 'rb')
    rej_strs = pickle.load(pick_handle)

    # Precompute the locations of manually raised errors and format the file properly
    global manual_errs
    manual_errs = argtracer.compute_base_ast(ar1, mut_dir + script_name + ".py")

    ar1 = mut_dir + script_name + ".py"

    # Get base values from the non-crashing run with the longest input
    basein = ""
    for cand in rej_strs:
        basein = cand[1] if len(cand[1]) > len(basein) else basein
    try:
        (_, b_cdict, b_vrs, err) = argtracer.trace(ar1, basein, timeout=timeout)
    except Timeout:
        print("Execution timed out on basestring! Try increasing timeout (currently", timeout," seconds)")

    if err:
    	raise SystemExit("Exiting: " + pick_file + " contains no valid inputs for " + ar1)
    print("Used baseinput:", repr(basein))

    # Run the mutation process for every rejected string
    for s in rej_strs:
        s = s[0]
        queue = [(ar1, [])]
        discarded = set()
        # Save which exception the first execution of the rejected string produced
        original_ex_str = None
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
            if berr:
                print("Mutation complete:", arg, "(base rejected)")
                mutants_with_cause.append((arg, "valid string rejected"))

            if original_ex_str is None:
                original_ex_str = str(err.__class__)

            (prim, sec) = get_left_diff(cdict, b_cdict)
            prim = [e for e in prim if e[0] not in history]
            sec = [e for e in sec if e[0] not in history]
            print("Used string:", repr(s))
            print("Difference to base (flipped):", prim)
            print("Difference to base (new):", sec)
            print("Final line:", str(lines[0]))
            print("")
            print("Change history:", history)
            if err:
            	# Check whether the exception is different from the first encountered one
            	diff_err = str(err.__class__) != original_ex_str
            	err = True
            print("Mutated string rejected:", err, "different:", diff_err)
            if err and not diff_err:
                if not berr:
                    # In case the base string is not rejected we discard the script, otherwise we can keep it
                	discarded.add(arg)
                all_fixes = get_possible_fixes((prim, sec), arg, b_vrs, vrs)
                if all_fixes:
                    for (fix_list, fix_line) in all_fixes:
                        # Create a mutant for every possible fix
                        for fix in fix_list:
                            if not fix.endswith("\n"):
                                fix = fix + "\n"
                            cand = mut_dir + script_name + "_" + str(str_cnt) + "_" + str(mut_cnt) + ".py"
                            mods = { fix_line : fix }
                            queue.append((cand, history.copy()+[fix_line]))
                            file_copy_replace(cand, arg, mods)
                            mut_cnt += 1
            # Stop the mutation when the originally rejected string is accepted
            elif arg != ar1:
            	print("Mutation complete:", arg, "(mutated string accepted)")
            	mutants_with_cause.append((arg, "mutated string accepted"))
            		
        # Don't delete the original script, we need it to create mutants from whenever a new rejected string is processed
        discarded.discard(ar1)
        # Remove all scripts that neither reject the base string nor accept the mutated string
        for scrpt in discarded:
            print("Removed:", scrpt)
            os.remove(scrpt)
        # Adjust the file naming
        str_cnt += 1
        mut_cnt = 0
        print("Processing string number:", str(str_cnt), "/", str(len(rej_strs)))
    # Remove the copy of the original script since it is not a mutant
    os.remove(ar1)
    print("Done. The final mutants are in:", mut_dir)
    # Write a log on why each file was kept. This way we (or check_results.py) can check whether the mutation procedure is working correctly.
    with open(mut_dir[:-1] + "_inputs.log", "w", encoding="UTF-8") as file:
            for i in range(len(rej_strs)):
                file.write(str(i) + ": " + repr(rej_strs[i][0])+"\n")
            file.write("The baseinput was: " + repr(basein))

    with open(mut_dir[:-1] + ".log", "w", encoding="UTF-8") as file:
        file.write("Mutating script: " + repr(orig_file) + "\n")
        for e in mutants_with_cause:
            file.write(repr(e) + "\n")

if __name__ == "__main__":
    main(sys.argv)