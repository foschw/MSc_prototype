#!/usr/bin/env python3
import sys
import pickle
import imp
from config import get_default_config
from generate_reject import bitflip, byteflip, trim, delete, insert, swap, RandomizedList
import random
import taintedstr

current_config = get_default_config()

def main(args):
    # Generate rejected input strings
    if len(args) < 4:
        raise SystemExit("Please specify: 'subject.py' 'output_file.bin' 'at least one valid string' as parameters")
    t_prog = args[1]
    # Adjust path to allow imports
    subpath = ""
    path_lst = t_prog.split("/")[:-1]
    for ele in path_lst:
        if subpath:
            subpath = subpath + ele + "/"
        else:
            subpath = ele + "/"
        sys.path.insert(0, subpath)
    outfile = args[2]
    resl = []
    # Parse program inputs from the command line
    for i in range(3,len(sys.argv)):
        resl.append(sys.argv[i])
    print(resl, flush=True)
    print(str(len(resl)), " valid element(s) parsed", flush=True)
    # Generate invalid strings
    resl = gen_invalid(resl, t_prog)
    resl = [e for e in resl]
    # Save the mutated strings in binary as a file
    res_file = open(outfile, mode='wb')
    pickle.dump(resl, res_file)
    res_file.close()

def gen_invalid(valid_strs, arg):
    global current_config
    # If the string is too short do not use mutators that shrink it further
    min_len = int(current_config["min_mut_len"])
    # Mutation attempts per generated string since mutations are cheap but generation is expensive
    mut_attempts = int(current_config["max_mut_attempts"])
    _mod = imp.load_source('mymod', arg)
    rejected = set()
    # Mutation operations well suited for short strings
    smutops = [bitflip, byteflip, insert]
    # Mutation operations for longer strings
    lmutops = [trim, delete, swap]
    mutops = smutops + lmutops
    valid_str_lst = RandomizedList([elemnt for elemnt in valid_strs])
    # The rough amount of attempts for the whole set of strings
    mut_acc = mut_attempts * len(valid_str_lst)
    while mut_acc > 0:
        # Limit the amount of output elements
        if len(rejected) >= 2*len(valid_str_lst):
            break
        a = valid_str_lst.get_random_element()
        # Mutate up to mut_attempts times
        for i in range(max(int(mut_acc/max(1,(len(valid_str_lst)-len(rejected)))),1)):
            mut_acc -= 1
            mutator = random.choice(smutops) if len(str(a)) <= min_len else random.choice(mutops)
            a1 = taintedstr.tstr(mutator(str(a)))
            try:        
                res = _mod.main(a1)
            except:
                print("Mutation result: ", repr(a1), "(", str(mutator), ")", flush=True)
                rejected.add((a1, a))
                break
            else:
                a = a1

    return rejected

if __name__ == "__main__":
    main(sys.argv)