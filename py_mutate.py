#!/usr/bin/env python3
import sys
import getopt
sys.path.append('.')
from generate_reject import main as gen
from find_mutation_lines import main as mutate
from check_results import main as check
from run_unittests import main as run_tests

def main(argv):
    # The argument order is: program path, binary input file, number of pychains iterations
    prog = argv[1] if argv[1].endswith(".py") else argv[1] + ".py"
    binfile = "rejected_" + prog[prog.rfind("/")+1:prog.rfind(".py")] + ".bin" if not argv[2] else argv[2]
    timelimit = 60 if not argv[3] else argv[3]
    timeout = 2 if not argv[4] else argv[4]
    # Generate inputs in case no binary file is supplied
    if not argv[2]:
        print("Generating input for:", prog, "...", flush=True)
        gen([None, prog, timelimit, binfile])
    # Otherwise use the given inputs
    else:
        print("Using inputs from:", binfile, flush=True)
    print("Starting mutation...", prog, flush=True)
    # Run the mutation algorithm
    mutate([None, prog, binfile, timeout])
    # Check whether the results are fine and remove potentially problematic scripts
    print("Testing result integrity...", flush=True)
    check([None, prog, binfile, True])
    # Finally run the program's test suite
    print("Running unittests...", flush=True)
    run_tests([None, prog])
    print()
    print("Done.")

if __name__ == "__main__":
    print('The arguments are: "program path" [, -b "binary input file", -t "time for generation (in s)", -l "timeout for mutant execution (in s)"]', flush=True)
    
    binfile = None
    timelimit = 60
    timeout = 2
    print(len(sys.argv))
    if len(sys.argv) < 2:
        raise SystemExit("Please specifiy a .py file as argument.")
    elif len(sys.argv) > 2 and not sys.argv[2].startswith("-"):
        raise SystemExit("Invalid parameter after script. \n Possible options: \n -b \"binary input file\", \n -t \"time for generation (in s)\", \n -l \"timeout for mutant execution (in s)\"")


    opts, args = getopt.getopt(sys.argv[2:], "b:t:l:")
    for opt, a in opts:
        if opt == "-b":
            print("Using binary file:", a, flush=True)
            binfile = a
        elif opt == "-t":
            timelimit = int(a)
        elif opt == "-l":
            timeout = int(a)

    main([sys.argv[0],sys.argv[1],binfile,timelimit,timeout])