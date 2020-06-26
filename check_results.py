#!/usr/bin/env python3
import sys
import subprocess
import re
import pickle
import os
from config import get_default_config
from tidydir import TidyDir as TidyDir
import shutil
import argtracer
import concurrent.futures

current_config = None

# Executes a .py file with a string argument and optionally a timeout.
# Returns the exception in case one occurred, "-1" if the execution failed and None otherwise.
def execute_script_with_argument(script, argument,tmout=None):
    if tmout is None:
        tmout = int(current_config["unittest_timeout_mt"])
    cmd = ["python", script, argument]
    try:
        proc = subprocess.Popen(cmd, shell=False,stderr=subprocess.PIPE)
        err = proc.communicate(timeout=tmout)[1].decode(sys.stderr.encoding)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.communicate()
        print("Warning:", script, "timed out.", flush=True)
        return "-1"
    except:
        return "-1"
    return extract_error_name(err)

# Extracts the error name from a traceback string
def extract_error_name(stderr_string):
    exc_name = None
    if not stderr_string:
        return exc_name

    if stderr_string.find("Traceback (most recent call last):") < 0:
        return "-1"
    
    err_arr = stderr_string.split("\n")
    for idx in reversed(range(len(err_arr))):
        if err_arr[idx] and (err_arr[idx].find(":") > 0 or not re.match(r"\s+", err_arr[idx])):
            exc_name = err_arr[idx].lstrip().rstrip()
            break
    if exc_name.find(":") > -1:
        exc_name = exc_name[:exc_name.find(":")]

    return exc_name

# Use threads as parallel execution of scripts can be independent
def exec_threaded(file, input):
    return execute_script_with_argument(file, input)

# Removes potentially invalid mutants based on the error list and fixes the log accordingly
def clean_and_fix_log(errs, logfile, sub_dir=None, script_base_name=None):
    tmp = logfile + "_"
    still_alive = set()
    with open(tmp, "w", encoding="UTF-8") as dest:
        with open(logfile, "r", encoding="UTF-8") as log:
            for num, line in enumerate(log):
                if num == 0:
                    dest.write(line)
                else:
                    scrpt, cause = eval(line)
                    if script_base_name:
                        scrpt = scrpt[:-3] + ("/" + sub_dir + "/").replace("//","/") + script_base_name
                    if not errs.get(scrpt) or cause.replace("string", "string not") not in errs.get(scrpt):
                        dest.write(line)
                        still_alive.add(scrpt)

    for fl in errs:
        if fl not in still_alive:
            if not script_base_name:
                os.remove(fl)
            else:
                fl = fl[:fl.rfind("/")+1]
                shutil.rmtree(fl)

    if os.path.exists(logfile + ".old"):
        os.remove(logfile + ".old")
    os.rename(logfile, logfile + ".old")
    os.rename(tmp, logfile)

# Determines which valid input string was used for the mutation procedure
def find_baseinput(ar1, mut_base_pairs):
    if argtracer.base_ast is None:
        if os.path.exists(ar1[:-3]+"_def.py"):
            raise SystemExit("Found file:'" + ar1[:-3]+"_def.py" + "' Please rename/remove this before running check_results to avoid clashes.")
        argtracer.compute_base_ast(ar1, ar1[:-3]+"_def.py")
    basein = None
    ln_cond = -1
    for cand in mut_base_pairs:
        try:
            (_,base_cond,_,_) = argtracer.trace(ar1, cand[1])
            if len(base_cond) > ln_cond:
                ln_cond = len(base_cond)
                basein = cand[1]
        except:
            pass

    if os.path.exists(ar1[:-3]+"_def.py"):
        os.remove(ar1[:-3]+"_def.py")

    return basein


def main(argv, qc=None):
    global current_config
    current_config = get_default_config()
    # Specify the original name of the script to check the results. 
    # Uses the second argument as binary input file, or the config value in case it is omitted.
    # The optional third argument controls whether the unverifiable scripts are to be removed.
    if len(argv) < 2:
        raise SystemExit("Please specify the script name!")

    base_dir = TidyDir("", guess=False)

    scriptname = argv[1] if not argv[1].endswith(".py") else argv[1][:argv[1].rfind(".py")]
    original_file = scriptname + ".py"
    script_base_name = original_file[original_file.rfind("/")+1:]
    (sub_dir, scrpt) = base_dir.split_path(scriptname)
    if scriptname.rfind("/"):
        scriptname = scriptname[scriptname.rfind("/")+1:]
    cause_file = str(TidyDir(current_config["default_mut_dir"])) + scriptname + ".log"
    test_log = str(TidyDir(current_config["default_mut_dir"])) + scriptname + "_test_results.log"
    inputs_file = current_config["default_rejected"] if len(argv) < 3 else argv[2]
    clean_invalid = int(current_config["default_clean_invalid"]) if len(argv) < 4 else argv[3]
    all_inputs = []
    all_mutants = []
    behave = {}
    mutant_to_cause = {}
    num_workers = int(current_config["test_threads"])
    run_seq = []

    with open(cause_file, "r", encoding="UTF-8") as causes:
        for num, line in enumerate(causes):
            # Get the path to the original script
            if num > 0:
                # Use eval to get the pair representation of the line. The first element is the mutant.
                the_mutant = eval(line)[0]
                the_mutant = the_mutant.replace("//","/")
                if not os.path.exists(the_mutant):
                    raise SystemExit("Could not find file: '" + the_mutant + "'.\nLog file: '" + cause_file + "' is corrupted.")
                adj_dir = base_dir if base_dir else scriptname[:scriptname.rfind("/")]
                effect_set = mutant_to_cause.get(the_mutant) if mutant_to_cause.get(the_mutant) else set()
                # Code mutant behaviour as integer for easy comparison
                if eval(line)[1].find("rejected") > -1:
                    effect_set.add(0)
                else:
                    effect_set.add(1)
                mutant_to_cause[the_mutant] = effect_set
                if the_mutant not in all_mutants:
                    all_mutants.append(the_mutant)

    qc = qc if qc is not None else int(current_config["quick_check"])
    if  qc > 0:
        all_mutants = []
        top_page = []
        with open(test_log, "r", encoding="UTF-8") as fl:
            lst = fl.read().split("\n")
        for idx in range(0,len(lst),3):
            e = lst[idx][:-1]
            if lst[idx+1].rstrip().endswith(r"Fail: 0"):
                if not os.path.exists(e):
                    raise SystemExit("Cannot find file:" + e)
                all_mutants.append(e)
                top_page.append(lst[idx])
                top_page.append(lst[idx+1])
                top_page.append(lst[idx+2])
            elif re.match(r"-+", lst[idx]) or re.findall(r"Fail: [123456789]+\d?", lst[idx+1]):
                rest = lst[idx:-1]
                break

    rej_strs = pickle.load(open(inputs_file, "rb"))
    basein = find_baseinput(original_file, rej_strs)
    inputs = []
    # Find the used base candidate
    for cand in rej_strs:
        inputs.append(str(cand[0]))

    errs = {}
    # Check whether the used valid string is actually valid
    exc_orig = execute_script_with_argument(original_file, basein)
    if exc_orig:
        raise SystemExit("Original script rejects baseinput: " + repr(basein))

    # Check all mutants for behaviour changes
    cnt = 1
    # Layout all detected behaviour linearly, each index triplet contains observed results of a mutated file
    mut_behaves = [0 for _ in range(3*len(all_mutants))]

    future_to_index = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as tpe:
        for i in range(0,len(mut_behaves),3):
            my_mutant = all_mutants[int(i/3)]
            # Find the used input
            my_input = my_mutant[:my_mutant.rfind("_")]
            my_input = inputs[int(my_input[my_input.rfind("_")+1:])]
            # Check whether the valid string is rejected
            future_to_index[tpe.submit(exec_threaded, my_mutant, basein)] = i
            # Check the output of the original script for the rejected string
            future_to_index[tpe.submit(exec_threaded, original_file, my_input)] = i+1 
            # Check the output of the mutated script for the rejected string
            future_to_index[tpe.submit(exec_threaded, my_mutant, my_input)] = i+2

        fidx = 0
        for future in concurrent.futures.as_completed(future_to_index):
            index = future_to_index[future]
            mut_behaves[index] = future.result()
            if future.result() == "-1":
                run_seq.append(index)
            if fidx % 3 == 0:
                print("Checking mutant:", str(1+int(fidx/3)) + "/" + str(len(all_mutants)), flush=True)
            fidx += 1

    seq_idx = 0
    if run_seq:
        print("Checking:", len(run_seq), "scripts in sequential mode....", flush=True)
        for sq_idx in run_seq:
            print("Checking script:", str(seq_idx+1), "/", str(len(run_seq)), flush=True)
            seq_idx += 1
            my_mutant = all_mutants[int(sq_idx/3)]
            sq_command = sq_idx % 3
            if sq_command == 0:
                mut_behaves[sq_idx] = execute_script_with_argument(my_mutant,basein,tmout=int(current_config["unittest_timeout"]))
            else:
                my_input = my_mutant[:my_mutant.rfind("_")]
                my_input = inputs[int(my_input[my_input.rfind("_")+1:])]
                if sq_command == 1:
                    mut_behaves[sq_idx] = execute_script_with_argument(original_file, my_input,tmout=int(current_config["unittest_timeout"]))
                else:
                    mut_behaves[sq_idx] = execute_script_with_argument(my_mutant, my_input,tmout=int(current_config["unittest_timeout"]))

    bhindex = 0
    while bhindex < len(mut_behaves):
        my_mutant = all_mutants[int(bhindex/3)]
        exc_mutant_valid = mut_behaves[bhindex]
        exc_orig_invalid = mut_behaves[bhindex+1]
        exc_mutant = mut_behaves[bhindex+2]
        # Organize the observed behaviour of the mutant
        if exc_mutant_valid and exc_mutant_valid != "-1":
            bh = behave.get(my_mutant) if behave.get(my_mutant) else []
            bh.append("valid string rejected")
            behave[my_mutant] = bh

        if not exc_mutant:
            bh = behave.get(my_mutant) if behave.get(my_mutant) else []
            bh.append("invalid string accepted")
            behave[my_mutant] = bh

        elif exc_orig_invalid != exc_mutant and exc_mutant != "-1" and exc_orig_invalid != "-1":
            bh = behave.get(my_mutant) if behave.get(my_mutant) else []
            bh.append("invalid string raises new exception")
            behave[my_mutant] = bh

        # Compare expected and actual behaviour
        for e in mutant_to_cause.get(my_mutant):
            if e == 0 and (not exc_mutant_valid or exc_mutant_valid == "-1"):
                er = errs.get(my_mutant) if errs.get(my_mutant) else []
                er.append("valid string not rejected")
                errs[my_mutant] = er
            elif e == 1 and ((exc_mutant and exc_mutant == "-1") or (exc_orig_invalid and exc_orig_invalid == "-1") or (exc_mutant and exc_orig_invalid and exc_mutant == exc_orig_invalid)):
                er = errs.get(my_mutant) if errs.get(my_mutant) else []
                er.append("mutated string not accepted")
                errs[my_mutant] = er

        bhindex += 3

    print()
    if not errs:
        print("No problems found.")
    else:
        print("Found", len(errs), "potential problem(s):")
        print(errs)

    if clean_invalid and errs:
        print()
        print("Removing potentially invalid scripts...")
        if str(base_dir) == "/":
            clean_and_fix_log(errs, cause_file)
        else:
            clean_and_fix_log(errs, cause_file, sub_dir, script_base_name)

    print()
    # Assign mutant class to scripts
    mut_0 = []
    mut_1 = []
    mut_2 = []
    for mut in behave:
        for bhvr in behave[mut]:
            if bhvr.find("rejected") >= 0:
                mut_0.append(mut)
            elif bhvr.find("raises") >= 0:
                mut_1.append(mut)
            elif bhvr.find("accepted") >= 0:
                mut_2.append(mut)

    behave_file = (current_config["default_mut_dir"]+"/").replace("//","/") + scriptname + "_verified.log"
    if os.path.exists(behave_file):
        os.remove(behave_file)
    with open(behave_file, "w", encoding="UTF-8") as dest:
        if mut_0:
            mut_0 = sorted(mut_0, key=by_index)
            dest.write("Valid string rejected:\n")
            for m_0 in mut_0:
                dest.write(repr(m_0) + "\n")
            dest.write("\n")
        if mut_1:
            mut_1 = sorted(mut_1, key=by_index)
            dest.write("Invalid string raises new exception:\n")
            for m_1 in mut_1:
                dest.write(repr(m_1) + "\n")
            dest.write("\n")
        if mut_2:
            mut_2 = sorted(mut_2, key=by_index)
            dest.write("Invalid string accepted:\n")
            for m_2 in mut_2:
                dest.write(repr(m_2) + "\n")

    if qc > 0:
        if all_mutants:
            for test_mut in all_mutants:
                if not os.path.exists(test_mut):
                    idx = top_page.index(test_mut+":")
                    # Delete the 3 lines belonging to this mutant
                    del top_page[idx]
                    del top_page[idx]
                    del top_page[idx]

            # Remove the - indicator line as there are no 0 fail mutants left
            if not top_page:
                rest = rest[2:]

            with open(test_log, "w", encoding="UTF-8") as dst:
                for ln in top_page + rest:
                    dst.write(ln+"\n")
                

def by_index(mutant_name):
    ky = re.findall(r"_\d+_\d+\.py$", mutant_name)[0][1:-3]
    return (int(ky[:ky.find("_")]), int(ky[ky.find("_")+1:]))

if __name__ == "__main__":
    main(sys.argv, qc=0)