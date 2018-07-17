#!/usr/bin/env python3
import sys
sys.path.append('.')
import pychains.chain
import imp
import taintedstr
import random
import pickle

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

def get_valid_inputs(arg, times):
    _mod = imp.load_source('mymod', arg)
    res = set()
    for i in range(times):
        print(i, "--------", flush=True)
        e = pychains.chain.Chain()
        try:
            (a, r) = e.exec_argument(_mod.main)
        except:
            print("Pychains encountered an error, skipping...", flush=True)
            taintedstr.reset_comparisons()
            continue
        res.add(a)
        print("Arg:", repr(a), flush=True)
        print("Eval:", repr(r), flush=True)    

    return res


def main(arg, times):
    # If the string is too short do not use mutators that shrink it further
    min_len = 5
    # Mutation attempts per generated string since mutations are cheap but generation is expensive
    mut_attempts = 100
    _mod = imp.load_source('mymod', arg)
    rejected = set()
    errs = set()
    smutops = [bitflip, byteflip, insert]
    lmutops = [trim, delete, swap]
    mutops = smutops + lmutops
    valid_strs = get_valid_inputs(arg, times)
    print("Got", len(valid_strs), "valid strings from pychains (", times, "iterations)")

    for a in valid_strs:

        for j in range(mut_attempts):
            mutator = random.choice(smutops) if len(str(a)) <= min_len else random.choice(mutops)
            a1 = taintedstr.tstr(mutator(str(a)))
            try:        
                res = _mod.main(a1)
            except Exception as ex:
                print("Mutation result: ", repr(a1), "(", str(mutator), ")", flush=True)
                rejected.add(a1)
                errs.add(ex.__class__.__name__)
                break
            else:
                a = a1

    return (rejected, errs)

if __name__ == "__main__":
    (res, errs) = main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 1)
    outfile = sys.argv[3] if len(sys.argv) > 3 else "rejected.bin"
    resl = []
    for r in res:
        resl.append(r)
    print(resl)
    print(str(len(resl)), " rejected elements created")
    print(errs)
    res_file = open(outfile, mode='wb')
    pickle.dump((resl, errs), res_file)
    res_file.close()
