#!/usr/bin/env python3
import sys
import subprocess
import re
import os
from config import get_default_config
from tidydir import TidyDir as TidyDir
import concurrent.futures
import glob
from find_mutation_lines import LogWriter

current_config = None

# Executes the test suite of a .py file optionally with a timeout
# Returns the amount of tests passed and failed as a pair
def run_unittests_for_script(script,tmout=None):
    if tmout is None:
        tmout = int(current_config["unittest_timeout_mt"])
    cmd = ["python", "-m", "unittest", script[script.rfind("/")+1:]]
    script_dir = os.path.abspath(script[:script.rfind("/")+1]).replace("\\","/")
    try:
        proc = subprocess.Popen(cmd, shell=False,stderr=subprocess.PIPE,cwd=script_dir)
        res = proc.communicate(timeout=tmout)[1].decode(sys.stderr.encoding)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.communicate()
        return (-1,None)
    except:
        raise SystemExit("Unit test execution failed.")
    return extract_test_stats(res, script)

# Extracts the total amount of test cases as well as the identifiers of the failed tests
def extract_test_stats(unittest_output, script):
    script = script if script.rfind("/") == -1 else script[script.rfind("/")+1:]
    if script.endswith(".py"):
        script = script[:-3]
    outpt_lines = unittest_output.lstrip().rstrip().split("\n")
    re_test_num = r"^Ran \d+ test(s)? in \d(\.)?\d*s"
    re_tstname = r"^=+$"
    total_tests = 0
    nxt = False
    ftest_names = set()
    for ol in outpt_lines:
        ol = ol.lstrip().rstrip()
        if nxt:
            ftest_names.add(generify_name(ol, script))
        if re.match(re_tstname, ol):
            nxt = True
        else:
            nxt = False

        if re.match(re_test_num, ol):
            total_tests = int(ol[4:ol.find("test")])

    return (total_tests, ftest_names)

def generify_name(line, script):
    line = line.lstrip().rstrip()
    res = line[line.find(":")+2:]
    res = res.replace("(" + script + ".", "(")
    return res

# Running tests can be done independently
def run_tests_threaded(script):
    return run_unittests_for_script(script)

def main(argv):
    global current_config
    current_config = get_default_config()
    # Specify the original name of the script or its path to check the results. 
    if len(argv) < 2:
        raise SystemExit("Please specify the folder the scripts are in!")
    argv[1] = argv[1].replace("\\", "/")
    argv[1] = argv[1][:-1] if argv[1].endswith("/") else argv[1]
    test_res_fl = argv[1] + "_test_results.log"
    mutant_fail_dict = argv[1] + "_fail_dict.log"
    lwriter = LogWriter(test_res_fl)
    scripts_f = []
    scripts_p = []
    targets = []
    mutant_to_testfail = {}
    num_workers = int(current_config["test_threads"])

    for fnm in glob.iglob(argv[1]+"/*.py", recursive=True):
        fnm = fnm.replace("\\","/")
        if fnm not in targets:
            targets.append(fnm)

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as tpe:
        future_to_script = {tpe.submit(run_tests_threaded, test_script) : test_script for test_script in targets}
        fidx = 0
        for future in concurrent.futures.as_completed(future_to_script):
            print("Running tests:", str(fidx+1) + "/" + str(len(targets)), flush=True)
            test_script = future_to_script[future]
            (testnum, failnames) = future.result()
            if failnames is not None:
                tpass = testnum-len(failnames)
                tfail = len(failnames)
                mutant_to_testfail[test_script] = failnames

            else:
                tpass = -1
                tfail = -1

            if tfail == 0:
                if tpass > 0:
                    scripts_p.append((test_script,(tpass,tfail)))
            else:
                    scripts_f.append((test_script,(tpass,tfail)))
            lwriter.append_line(test_script + ":\nPass: " + str(tpass) + ", Fail: " + str(tfail) + " \n" + "\n")
            fidx += 1

    # Write the test stats to a file. Mutants that fail no tests are at the top if they exist.
    with open(test_res_fl, "w", encoding="UTF-8") as dest:
        scripts_p = sorted(scripts_p, key=by_index)
        for (scrpt, (tpass,tfail)) in scripts_p:
            dest.write(scrpt + ":\nPass: " + str(tpass) + ", Fail: " + str(tfail) + " \n")
            dest.write("\n")

        if scripts_p and scripts_f:
            dest.write("---------------------------------------------------------------------------------------------------\n")
            dest.write("\n")

        scripts_f = sorted(sorted(scripts_f, key=by_index), key=by_fail)

        for (scrpt, (tpass,tfail)) in scripts_f:
            dest.write(scrpt + ":\nPass: " + str(tpass) + ", Fail: " + str(tfail) + " \n")
            dest.write("\n")

    # Log which tests the mutants failed to enable minimal mutant set generation
    with open(mutant_fail_dict, "w", encoding="UTF-8") as dest:
        dest.write(repr(mutant_to_testfail))

def by_fail(result):
    (_, (_, tfail)) = result
    rv = tfail if tfail >= 0 else float("inf")
    return rv

def by_index(result):
    (mutant_name, _) = result
    ky = re.findall(r"_\d+_\d+\.py$", mutant_name)
    if len(ky) != 1:
        return mutant_name
    ky = ky[0][1:-3]
    return (int(ky[:ky.find("_")]), int(ky[ky.find("_")+1:]))

if __name__ == "__main__":
    main(sys.argv)