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

current_config = None

def main(argv):
    global current_config
    current_config = get_default_config()
    prog = argv[1] if argv[1].endswith(".py") else argv[1] + ".py"
    binfile = "rejected_" + prog[prog.rfind("/")+1:prog.rfind(".py")] + ".bin" if not argv[2] else argv[2]
    timelimit = int(current_config["default_gen_time"]) if not argv[3] else argv[3]
    timeout = int(current_config["min_timeout"]) if not argv[4] else argv[4]
    seed = None if not argv[5] else argv[5]

    # Generate inputs in case no binary file is supplied
    if not argv[2]:
        instr_code = rewrite_ast(prog)
        target_loc = prog[:-3] + "_instr.py"
        with open(target_loc, "w", encoding="UTF-8") as inst_out:
            inst_out.write(instr_code)
        print("Generating inputs for:", prog, "...", flush=True)
        gen([None, target_loc, timelimit, binfile],seed)
    # Otherwise use the given inputs
    else:
        print("Using inputs from:", binfile, flush=True)
    print("Starting mutation...", prog, "(Timestamp: '" + str(datetime.datetime.now()) + "')", flush=True)
    # Run the mutation algorithm
    mutate([None, prog, binfile, timeout], seed)
    # Check whether the results are fine and remove potentially problematic scripts
    print("Testing result integrity...", flush=True)
    check([None, prog, binfile, True])
    # Finally run the program's test suite
    print("Running unittests...", flush=True)
    run_tests([None, prog])
    print()
    print("Done.", "(Timestamp: '" + str(datetime.datetime.now()) + "')", flush=True)

if __name__ == "__main__":
    print('The arguments are: "program path" [, -b "binary input file", -t "time for generation (in s)", -l "timeout for mutant execution" (in s), -d "directory to use as base"]', flush=True)
    
    binfile = None
    timelimit = None
    timeout = None
    seed = None
    if len(sys.argv) < 2:
        raise SystemExit("Please specifiy a .py file as argument.")
    elif len(sys.argv) > 2 and not sys.argv[2].startswith("-"):
        raise SystemExit("Invalid parameter after script. \n Possible options: \n -b \"binary input file\", \n -t \"time for generation (in s)\", \n -l \"timeout for mutant execution (in s)")


    opts, args = getopt.getopt(sys.argv[2:], "b:t:l:s:")
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

    main([sys.argv[0],sys.argv[1],binfile,timelimit,timeout,seed])