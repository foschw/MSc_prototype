#!/usr/bin/env python3
import sys
import getopt
sys.path.append('.')
from generate_reject import main as gen
from find_mutation_lines import main as mutate
from check_results import main as check
from run_unittests import main as run_tests
from craft_runnable_mutant import main as craft
from config import get_default_config
from adjust_imports import main as adjust
from tidydir import TidyDir as TidyDir

current_config = None

def main(argv):
    global current_config
    current_config = get_default_config()
    prog = argv[1] if argv[1].endswith(".py") else argv[1] + ".py"
    binfile = "rejected_" + prog[prog.rfind("/")+1:prog.rfind(".py")] + ".bin" if not argv[2] else argv[2]
    timelimit = int(current_config["default_gen_time"]) if not argv[3] else argv[3]
    timeout = int(current_config["min_timeout"]) if not argv[4] else argv[4]
    base_dir = None if not argv[5] else TidyDir(argv[5])

    adj_dir = str(base_dir) if base_dir else str(TidyDir(prog))
    input_sub = prog.replace(adj_dir,adj_dir[:-1]+"_stripped/") if not argv[6] else argv[6]
    if not input_sub.endswith(".py"):
        input_sub = input_sub + ".py"
    print("Adjusting imports...", adj_dir, flush=True)
    adjust([None, adj_dir, None])
    # Generate inputs in case no binary file is supplied
    if not argv[2]:
        print("Generating inputs for:", prog, "...", flush=True)
        gen([None, input_sub, timelimit, binfile])
    # Otherwise use the given inputs
    else:
        print("Using inputs from:", binfile, flush=True)
    print("Starting mutation...", prog, flush=True)
    # Add the script's base directory and its subdirectories to path
    if base_dir:
        for mypath in base_dir.get_subdirs():
            sys.path.append(mypath)
    # Run the mutation algorithm
    mutate([None, prog.replace(adj_dir,adj_dir[:-1]+"_stripped/"), binfile, timeout])
    # Create full copy of project to make each mutant runnable (requires -d)
    if base_dir:
        print("Renaming and copying required files....")
        craft([None, prog, base_dir])
    # Check whether the results are fine and remove potentially problematic scripts
    print("Testing result integrity...", flush=True)
    check([None, prog, binfile, base_dir, True])
    # Finally run the program's test suite
    print("Running unittests...", flush=True)
    run_tests([None, prog, base_dir])
    print()
    print("Done.")

if __name__ == "__main__":
    print('The arguments are: "program path" [, -b "binary input file", -t "time for generation (in s)", -l "timeout for mutant execution" (in s), -d "directory to use as base"]', flush=True)
    
    binfile = None
    timelimit = None
    timeout = None
    base_dir = None
    input_sub = None
    print(len(sys.argv))
    if len(sys.argv) < 2:
        raise SystemExit("Please specifiy a .py file as argument.")
    elif len(sys.argv) > 2 and not sys.argv[2].startswith("-"):
        raise SystemExit("Invalid parameter after script. \n Possible options: \n -b \"binary input file\", \n -t \"time for generation (in s)\", \n -l \"timeout for mutant execution (in s)\", \n , -d \"directory to use as base\", \n -i \"path to preprocessed subject\"")


    opts, args = getopt.getopt(sys.argv[2:], "b:t:l:d:i:")
    for opt, a in opts:
        if opt == "-b":
            print("Using binary file:", a, flush=True)
            binfile = a
        elif opt == "-t":
            timelimit = int(a)
        elif opt == "-l":
            timeout = int(a)
        elif opt == "-d":
            base_dir = a
        elif opt == "-i":
            input_sub = a

    main([sys.argv[0],sys.argv[1],binfile,timelimit,timeout,base_dir,input_sub])