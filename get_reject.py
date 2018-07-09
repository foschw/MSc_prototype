#!/usr/bin/env python3
import sys
sys.path.append('.')
import pychains.chain
import imp
import taintedstr
import random

if __name__ == "__main__":
    # If the string is too short do not use mutators that shrink it further
    arg = sys.argv[1]
    times = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    _mod = imp.load_source('mymod', "gemerate_reject")
    smutops = [bitflip, insert]
    lmutops = [byteflip, trim, delete, swap]
    mutops = smutops + lmutops

    for i in range(times):
        e = pychains.chain.Chain()
        (a, r) = e.exec_argument(_mod.main)
        mutator = random.choice(smutops) if len(str(a)) <= min_len else random.choice(mutops)
        a1 = mutator(str(a))
        print("Mutation result: ", a1, "(", str(mutator), ")", flush=True)
        try:        
            res = _mod.main(taintedstr.tstr(a1))
        except:
            print("Argument was rejected!")
            rejected.append(a1)    
        else: 
            print("Mutated argument still valid ", "(eval = ", res , ")")

        print("Arg:", repr(a), flush=True)
        print("Eval:", repr(r), flush=True)
        taintedstr.reset_comparisons()
    
    return rejected
