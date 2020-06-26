#!/usr/bin/env python3
import sys
import pickle

def main(args):
    # Generate rejected input strings
    if len(args) < 3:
        raise SystemExit("Please specify the output file and at least one pair as parameters")
    outfile = args[1]
    resl = []
    # Parse the following arguments as pairs of (rejected input, valid input)
    for i in range(2,len(sys.argv)):
        resl.append(eval(sys.argv[i]))
    print(resl, flush=True)
    print(str(len(resl)), " rejected element(s) parsed", flush=True)
    # Save the mutated strings in binary as a file
    res_file = open(outfile, mode='wb')
    pickle.dump(resl, res_file)
    res_file.close()

if __name__ == "__main__":
    main(sys.argv)