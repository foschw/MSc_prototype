#!/usr/bin/env python3
import sys
sys.path.append('.')
import pychains.chain
import imp
import taintedstr
import random

def bitflip(text):
    # Do not mutate if the input is not big enough
    if len(text) < 1:
        return text
    try:
        p = random.randint(0, len(text) -1)
    except ValueError:
        p = 0
    b = random.randint(0, 6)
    res = chr(ord(text[p]) ^ (1 << b))
    return text[:p] + res + text[p + 1:]

def byteflip(text):
    if len(text) < 2:
        return text
    try:
        p = random.randint(0, len(text) - 2)
    except ValueError:
        p = 0
    return text[:p] + text[p + 1] + text[p] + text[p + 2 :]

def trim(text):
    if len(text) < 1:
        return text
    try:
        newlen = random.randint(0, len(text) - 1)
    except ValueError:
        newlen = 0
    return text[:newlen]

def delete(text):
    if len(text) < 1:
        return ""
    try:
        p = random.randint(0, len(text)-1)
    except ValueError:
        p = 0
    return text[:p] + text[p+1:]

def insert(text):
    try:
        p = random.randint(0, len(text))
    except ValueError:
        p = 0
    rbyte = chr(int(random.random() * 255))
    return text[:p] + rbyte + text[p:]

def swap(text):
    if len(text) < 2:
        return text
    indexes = []
    for i in range(0, len(text)):
        indexes.append(i)
    p1 = random.choice(indexes)
    indexes.remove(p1)
    p2 = random.choice(indexes)
    s = min(p1, p2)
    e = max(p1, p2)
    b1 = text[s]
    b2 = text[e]
    return text[:s] + b2 + text[s+1:e] + b1 + text[e+1:]

def main(arg, times):
    # If the string is too short do not use mutators that shrink it further
    min_len = 5
    # Mutation attempts per generated string since mutations are cheap but generation is expensive
    mut_attempts = 100
    _mod = imp.load_source('mymod', arg)
    rejected = set()
    smutops = [bitflip, insert]
    lmutops = [byteflip, trim, delete, swap]
    mutops = smutops + lmutops

    for i in range(times):
        print(i, "--------", flush=True)
        e = pychains.chain.Chain()
        (a, r) = e.exec_argument(_mod.main)
        for j in range(mut_attempts):
            mutator = random.choice(smutops) if len(str(a)) <= min_len else random.choice(mutops)
            a1 = taintedstr.tstr(mutator(str(a)))
            print("Mutation result: ", repr(a1), "(", str(mutator), ")", flush=True)
            try:        
                res = _mod.main(a1)
            except:
                print("Argument was rejected!", flush=True)
                rejected.add(a1)    
                break
            else: 
                print("Mutated argument still valid ", "(eval = ", res , ")", flush=True)

        print("Arg:", repr(a), flush=True)
        print("Eval:", repr(r), flush=True)
        taintedstr.reset_comparisons()
    
    return rejected

if __name__ == "__main__":
    res = main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 1)
    print(res)
    print(str(len(res)), " rejected elements created")
