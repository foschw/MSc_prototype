#!/usr/bin/env python3
import sys
sys.path.append('.')
import pychains.chain
import imp
import taintedstr
import random
import pickle
from timeit import default_timer as timer
from config import get_default_config

current_config = None

# A class that allows retrieving list elements in a wrapping manner. 
# Once an element is retrieved it will not appear again until each other element was returned once.
class RandomizedList:
    def __init__(self, content):
        self.content = content
        self.offset = 0

    # Returns a random element from the list with repetition only possible after all other elements were retrieved
    def get_random_element(self):
        if len(self.content) - self.offset == 1:
            res = self.content[0]
            self.offset = 0
        else:
            pos = random.choice(range(len(self.content)-self.offset))
            res = self.content[pos]
            self.offset += 1
            tmp = self.content[len(self.content)-self.offset]
            self.content[pos] = tmp
            self.content[len(self.content)-self.offset] = res

        return res

    # Returns the length of the internal list
    def __len__(self):
        return len(self.content)

# The usual mutation operations introduced in Security Testing
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

# Run pychains for roughly timelimit seconds to get valid inputs
def get_valid_inputs(arg, timelimit):
    global current_config
    _mod = imp.load_source('mymod', arg)
    res = set()
    start = timer()
    best_time = 0
    overhead_const = float(current_config["best_overhead"])
    while timelimit > overhead_const*best_time:
        print(timelimit, "--------", flush=True)
        start_chain = timer()
        e = pychains.chain.Chain()
        try:
            (a, r) = e.exec_argument(_mod.main)
        except:
            print("Pychains encountered an error, skipping...", flush=True)
            continue
        finally:
            time_elapsed = timer() - start_chain
            taintedstr.reset_comparisons()
            if time_elapsed < best_time or best_time == 0:
                best_time = time_elapsed
            timelimit -= time_elapsed
        res.add(a)
        print("Arg:", repr(a), flush=True)
        print("Eval:", repr(r), flush=True)    

    return res

# Generate rejected strings by applying mutation operations
def gen(arg, timelimit, valid_strs=None):
    global current_config
    # Mutation attempts per generated string since mutations are cheap but generation is expensive
    max_rej = int(timelimit)
    mut_attempts = int(current_config["max_mut_attempts"])
    _mod = imp.load_source('mymod', arg)
    rejected = set()
    # Mutation operations for strings of any length
    l_mutops = [bitflip, byteflip, insert]
    # Mutation operations for strings with length > 1
    l2_mutops = [swap]
    # Mutation operations for strings with length > 0
    l1_mutops = [trim, delete]
    valid_strs = valid_strs if valid_strs else get_valid_inputs(arg, timelimit)
    valid_str_lst = RandomizedList([elemnt for elemnt in valid_strs])
    print("Got", len(valid_strs), "valid strings from pychains (" + str(timelimit) + " s)")
    max_rej = max(max_rej, 2*len(valid_strs))
    # The rough amount of attempts for the whole set of strings
    mut_acc = mut_attempts * len(valid_str_lst)
    while mut_acc > 0:
        # Limit the amount of output elements
        if len(rejected) >= max_rej:
            break
        a = valid_str_lst.get_random_element()
        # Mutate up to mut_attempts times
        for i in range(max(int(mut_acc/max(1,(len(valid_str_lst)-len(rejected)))),1)):
            mut_acc -= 1
            if len(str(a)) > 1:
                mutops = l_mutops + l2_mutops + l1_mutops
            elif len(str(a)) == 1:
                mutops = l_mutops + l1_mutops
            else:
                mutops = l_mutops
            mutator = random.choice(mutops)
            a1 = str(mutator(str(a)))
            try:        
                res = _mod.main(a1)
            except:
                print("Mutation result: ", repr(a1), "(", str(mutator), ")", flush=True)
                rejected.add((a1, a))
                break
            else:
                a = a1

    return rejected

def main(args, seed=None):
    random.seed(seed)
    # Read the config
    global current_config
    if not current_config:
        current_config = get_default_config()
    # Add the subject's path to sys.path
    sys.path.insert(0, args[1][:args[1].rfind("/")+1])
    # Generate rejected input strings
    if len(args) > 4 and args[4]:
        with open(args[4], "r", encoding="UTF-8") as vf:
            valid_ins = eval(vf.read())
    else:
        valid_ins = None
    res = gen(args[1], int(args[2]) if len(args) > 2 else int(current_config["default_gen_time"]), valid_strs=valid_ins)
    outfile = args[3] if len(args) > 3 else current_config["default_rejected"]
    resl = []
    for r in res:
        resl.append(r)
    print("All generated strings:", resl, flush=True)
    print(str(len(resl)), " rejected elements created", flush=True)
    # Save the mutated strings in binary as a file
    res_file = open(outfile, mode='wb')
    pickle.dump(resl, res_file)
    res_file.close()

if __name__ == "__main__":
    main(sys.argv)