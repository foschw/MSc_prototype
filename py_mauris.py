#!/usr/bin/env python3
import sys
import getopt
sys.path.append('.')
from generate_reject import main as gen
from find_mutation_lines import main as mutate
from check_results import main as check
from run_unittests import main as run_tests
from config import get_default_config
from tidydir import TidyDir as TidyDir
from rewrite_ast import rewrite_in as rewrite_ast
import datetime
import random
from filter_bin import main as convert_with_filter

current_config = None

def main(argv):
    global current_config
    current_config = get_default_config()
    prog = argv[1] if argv[1].endswith(".py") else argv[1] + ".py"
    binfile = "rejected_" + prog[prog.rfind("/")+1:prog.rfind(".py")] + ".bin" if not argv[2] else argv[2]
    timelimit = int(current_config["default_gen_time"]) if not argv[3] else argv[3]
    timeout = int(current_config["min_timeout"]) if not argv[4] else argv[4]
    seed = None if not argv[5] else argv[5]
    valid_file = None if not argv[6] else argv[6]
    filter_py = None if not argv[7] else argv[7]
    if filter_py:
        filter_py = filter_py if filter_py.endswith(".py") else filter_py + ".py"

    if seed is None:
        random.seed()
        # A random 32 bit integer
        seed = random.randrange(2**31-1)

    # Generate inputs in case no binary file is supplied
    if not argv[2]:
        tprog = filter_py if filter_py else prog
        instr_code = rewrite_ast(tprog)
        target_loc = tprog[:-3] + "_instr.py"
        with open(target_loc, "w", encoding="UTF-8") as inst_out:
            inst_out.write(instr_code)
        print("Generating inputs for:", tprog, "...", flush=True)
        gen([None, target_loc, timelimit, binfile, valid_file],seed)
    # Otherwise use the given inputs
    else:
        print("Using inputs from:", binfile, flush=True)

    if filter_py:
        print("Filtering inputs...", flush=True)
        convert_with_filter(prog, binfile, binfile)

    print("Starting mutation...", prog, "(Timestamp: '" + str(datetime.datetime.now()) + ", seed: " + str(seed) + "')", flush=True)
    # Run the mutation algorithm
    mutate([None, prog, binfile, timeout], seed)
    # Check whether the results are fine and remove potentially problematic scripts
    print("Testing result integrity...", flush=True)
    check([None, prog, binfile, True])
    # Finally run the program's test suite
    print("Running unit tests...", flush=True)
    run_tests([None, current_config["default_mut_dir"] + prog[prog.rfind("/")+1:-3]+"/"])
    print()
    print("Done.", "(Timestamp: '" + str(datetime.datetime.now()) + "')", flush=True)

if __name__ == "__main__":
    print('The arguments are: "program path" [, -b "binary input file", -t "time for generation (in s)", -l "timeout for mutant execution" (in s), -d "directory to use as base"]', flush=True)
    
    binfile = None
    timelimit = None
    timeout = None
    seed = None
    valid_file = None
    filter_py = None
    if len(sys.argv) < 2:
        raise SystemExit("Please specify a .py file as argument.")
    elif len(sys.argv) > 2 and not sys.argv[2].startswith("-"):
        raise SystemExit("Invalid parameter after script. \n Possible options: \n -b \"binary input file\", \n -t \"time for generation (in s)\", \n -l \"timeout for mutant execution (in s)\",\n -s \"random seed\",\n \"-v file_with_valid_inputs\",\n -f \"program with similar inputs\"")

    opts, args = getopt.getopt(sys.argv[2:], "b:t:l:s:v:f:")
    for opt, a in opts:
        if opt == "-b":
            print("Using binary file:", a, flush=True)
            binfile = a
        elif opt == "-t":
            timelimit = int(a)
        elif opt == "-l":
            timeout = int(a)
        elif opt == "-s":
            seed = int(a)
        elif opt == "-v":
            valid_file = a
        elif opt == "-f":
            filter_py = a

    main([sys.argv[0],sys.argv[1],binfile,timelimit,timeout,seed,valid_file,filter_py])