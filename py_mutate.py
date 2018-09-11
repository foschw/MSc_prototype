#!/usr/bin/env python3
import sys
import getopt
sys.path.append('.')
from generate_reject import main as gen
from find_mutation_lines import main as mutate
from check_results import main as check

def main(argv):
    # The argument order is: program path, binary input file, number of pychains iterations
    prog = argv[1] if argv[1].endswith(".py") else argv[1] + ".py"
    binfile = "rejected_" + prog[prog.rfind("/")+1:prog.rfind(".py")] + ".bin" if not argv[2] else argv[2]
    iterations = 1000 if not argv[3] else argv[3]
    if not argv[2]:
        print("Generating input for:", prog, "...")
        gen([None, prog, iterations, binfile])
    else:
        print("Using inputs from:", binfile)
    print("Starting mutation...", prog)
    mutate([None, prog, binfile])
    print("Testing result integrity...")
    check([None, prog, binfile])

if __name__ == "__main__":
    print('The arguments are: "program path" [, -b "binary input file", -i "number of pychains iterations"]', flush=True)
    
    binfile = None
    iterations = None

    if len(sys.argv) < 2:
        raise SystemExit("Please specifiy a .py file as argument.")

    opts, args = getopt.getopt(sys.argv[2:], "b:i:")
    for opt, a in opts:
        if opt == "-b":
            print("Using binary file:", a, flush=True)
            binfile = a
        elif opt == "-i":
            iterations = int(a)

    main([sys.argv[0],sys.argv[1],binfile,iterations])