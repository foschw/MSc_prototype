#!/usr/bin/env python3
import sys
sys.path.append('.')
import taintedstr
import pickle
import re
import argtracer
from argtracer import Timeout as Timeout
import random
import os
import glob
import imp
from timeit import default_timer as timer
from config import get_default_config
import ast
import astunparse
from math import floor
import functools

current_config = None

# Default mutation: replace ast elements with syntactically valid alternatives

class MutTransformer(ast.NodeTransformer):
    def __init__(self, trgt_code):
        super().__init__()
        self.target = trgt_code
        self.idx = 0

    # Binary Operators
    def visit_Add(self, tree_node):
        self.idx += 1
        if self.target[self.idx-1] == "1":
            ops = [ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow, ast.LShift, ast.RShift, ast.BitOr, ast.BitXor, ast.BitAnd, ast.FloorDiv]
            return self.generic_visit(random.choice(ops)())

        return self.generic_visit(tree_node)

    def visit_Sub(self, tree_node):
        self.idx += 1
        if self.target[self.idx-1] == "1":
            ops = [ast.Add, ast.Mult, ast.Div, ast.Mod, ast.Pow, ast.LShift, ast.RShift, ast.BitOr, ast.BitXor, ast.BitAnd, ast.FloorDiv]
            return self.generic_visit(random.choice(ops)())

        return self.generic_visit(tree_node)

    def visit_Mult(self, tree_node):
        self.idx += 1
        if self.target[self.idx-1] == "1":
            ops = [ast.Add, ast.Sub, ast.Div, ast.Mod, ast.Pow, ast.LShift, ast.RShift, ast.BitOr, ast.BitXor, ast.BitAnd, ast.FloorDiv]
            return self.generic_visit(random.choice(ops)())

        return self.generic_visit(tree_node)

    def visit_Div(self, tree_node):
        self.idx += 1
        if self.target[self.idx-1] == "1":
            ops = [ast.Add, ast.Sub, ast.Mult, ast.Mod, ast.Pow, ast.LShift, ast.RShift, ast.BitOr, ast.BitXor, ast.BitAnd, ast.FloorDiv]
            return self.generic_visit(random.choice(ops)())

        return self.generic_visit(tree_node)

    def visit_Mod(self, tree_node):
        self.idx += 1
        if self.target[self.idx-1] == "1":
            ops = [ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.LShift, ast.RShift, ast.BitOr, ast.BitXor, ast.BitAnd, ast.FloorDiv]
            return self.generic_visit(random.choice(ops)())

        return self.generic_visit(tree_node)

    def visit_Pow(self, tree_node):
        self.idx += 1
        if self.target[self.idx-1] == "1":
            ops = [ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.LShift, ast.RShift, ast.BitOr, ast.BitXor, ast.BitAnd, ast.FloorDiv]
            return self.generic_visit(random.choice(ops)())

        return self.generic_visit(tree_node)

    def visit_LShift(self, tree_node):
        self.idx += 1
        if self.target[self.idx-1] == "1":
            ops = [ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow, ast.RShift, ast.BitOr, ast.BitXor, ast.BitAnd, ast.FloorDiv]
            return self.generic_visit(random.choice(ops)())

        return self.generic_visit(tree_node)

    def visit_RShift(self, tree_node):
        self.idx += 1
        if self.target[self.idx-1] == "1":
            ops = [ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow, ast.LShift, ast.BitOr, ast.BitXor, ast.BitAnd, ast.FloorDiv]
            return self.generic_visit(random.choice(ops)())

        return self.generic_visit(tree_node)

    def visit_BitOr(self, tree_node):
        self.idx += 1
        if self.target[self.idx-1] == "1":
            ops = [ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow, ast.LShift, ast.RShift, ast.BitXor, ast.BitAnd, ast.FloorDiv]
            return self.generic_visit(random.choice(ops)())

        return self.generic_visit(tree_node)

    def visit_BitXor(self, tree_node):
        self.idx += 1
        if self.target[self.idx-1] == "1":
            ops = [ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow, ast.LShift, ast.RShift, ast.BitOr, ast.BitAnd, ast.FloorDiv]
            return self.generic_visit(random.choice(ops)())

        return self.generic_visit(tree_node)

    def visit_BitAnd(self, tree_node):
        self.idx += 1
        if self.target[self.idx-1] == "1":
            ops = [ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow, ast.LShift, ast.RShift, ast.BitOr, ast.BitXor, ast.FloorDiv]
            return self.generic_visit(random.choice(ops)())

        return self.generic_visit(tree_node)

    def visit_FloorDiv(self, tree_node):
        self.idx += 1
        if self.target[self.idx-1] == "1":
            ops = [ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow, ast.LShift, ast.RShift, ast.BitOr, ast.BitXor, ast.BitAnd]
            return self.generic_visit(random.choice(ops)())

        return self.generic_visit(tree_node)

    # Constants
    def visit_Num(self, tree_node):
        self.idx += 1
        if self.target[self.idx-1] == "1":
            rn = tree_node.n
            # Choose a random number between -|n|-1 and |n|+1. This may introduce a new ast element (unary minus)
            while rn == tree_node.n:
                rn = random.randint(-abs(tree_node.n)-1,abs(tree_node.n)+1)
            tree_node.n = rn

        return self.generic_visit(tree_node)

    # Boolean Operators
    def visit_And(self, tree_node):
        self.idx += 1
        if self.target[self.idx-1] == "1":
            return self.generic_visit(ast.Or())

        return self.generic_visit(tree_node)

    def visit_Or(self, tree_node):
        self.idx += 1
        if self.target[self.idx-1] == "1":
            return self.generic_visit(ast.And())

        return self.generic_visit(tree_node)

    # Comparisons
    def visit_Eq(self, tree_node):
        self.idx += 1
        if self.target[self.idx-1] == "1":
            return self.generic_visit(random.choice([ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.Is, ast.IsNot, ast.In, ast.NotIn])())

        return self.generic_visit(tree_node)

    def visit_NotEq(self, tree_node):
        self.idx += 1
        if self.target[self.idx-1] == "1":
            return self.generic_visit(random.choice([ast.Eq, ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.Is, ast.IsNot, ast.In, ast.NotIn])())

        return self.generic_visit(tree_node)

    def visit_Lt(self, tree_node):
        self.idx += 1
        if self.target[self.idx-1] == "1":
            return self.generic_visit(random.choice([ast.Eq, ast.NotEq, ast.LtE, ast.Gt, ast.GtE, ast.Is, ast.IsNot, ast.In, ast.NotIn])())

        return self.generic_visit(tree_node)

    def visit_LtE(self, tree_node):
        self.idx += 1
        if self.target[self.idx-1] == "1":
            return self.generic_visit(random.choice([ast.Eq, ast.NotEq, ast.Lt, ast.Gt, ast.GtE, ast.Is, ast.IsNot, ast.In, ast.NotIn])())

        return self.generic_visit(tree_node)

    def visit_Gt(self, tree_node):
        self.idx += 1
        if self.target[self.idx-1] == "1":
            return self.generic_visit(random.choice([ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.GtE, ast.Is, ast.IsNot, ast.In, ast.NotIn])())

        return self.generic_visit(tree_node)

    def visit_GtE(self, tree_node):
        self.idx += 1
        if self.target[self.idx-1] == "1":
            return self.generic_visit(random.choice([ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.Is, ast.IsNot, ast.In, ast.NotIn])())

        return self.generic_visit(tree_node)

    def visit_Is(self, tree_node):
        self.idx += 1
        if self.target[self.idx-1] == "1":
            return self.generic_visit(random.choice([ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.IsNot, ast.In, ast.NotIn])())

        return self.generic_visit(tree_node)

    def visit_IsNot(self, tree_node):
        self.idx += 1
        if self.target[self.idx-1] == "1":
            return self.generic_visit(random.choice([ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.Is, ast.In, ast.NotIn])())

        return self.generic_visit(tree_node)

    def visit_In(self, tree_node):
        self.idx += 1
        if self.target[self.idx-1] == "1":
            return self.generic_visit(random.choice([ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.Is, ast.IsNot, ast.NotIn])())

        return self.generic_visit(tree_node)

    def visit_NotIn(self, tree_node):
        self.idx += 1
        if self.target[self.idx-1] == "1":
            return self.generic_visit(random.choice([ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.Is, ast.IsNot, ast.In])())

        return self.generic_visit(tree_node)

    # Unary Operators excluding not
    def visit_Invert(self, tree_node):
        self.idx += 1
        if self.target[self.idx-1] == "1":
            return self.generic_visit(random.choice([ast.UAdd,ast.USub])())

        return self.generic_visit(tree_node)

    def visit_UAdd(self, tree_node):
        self.idx += 1
        if self.target[self.idx-1] == "1":
            return self.generic_visit(random.choice([ast.Invert,ast.USub])())

        return self.generic_visit(tree_node)

    def visit_USub(self, tree_node):
        self.idx += 1
        if self.target[self.idx-1] == "1":
            return self.generic_visit(random.choice([ast.Invert,ast.UAdd])())

        return self.generic_visit(tree_node)

    # Slice operators
    def visit_Slice(self, tree_node):
        self.idx += 1
        if self.target[self.idx-1] == "1":
            tree_node.lower = None
            tree_node.upper = None
            tree_node.step = None

        return self.generic_visit(tree_node)

# Counts how many mutation combinations are possible
class MutVisit(ast.NodeVisitor):
    def __init__(self):
        super().__init__()
        self.mod_cnt = 0

    # Arithmetic Operator
    def visit_BinOp(self, tree_node):
        self.mod_cnt += 1
        self.generic_visit(tree_node)

    # Constant
    def visit_Num(self, tree_node):
        self.mod_cnt += 1
        self.generic_visit(tree_node)

    # Logical (Boolean) Operator (and/or)
    def visit_BoolOp(self, tree_node):
        self.mod_cnt += 1
        self.generic_visit(tree_node)

    # Logical Operator (Compare)
    def visit_Compare(self, tree_node):
        self.mod_cnt += 1
        self.generic_visit(tree_node)

    # Unary Operator
    def visit_UnaryOp(self, tree_node):
        # Not is handled in a different way
        if not isinstance(tree_node.op, ast.Not):
            self.mod_cnt += 1
        self.generic_visit(tree_node)

    # Slice
    def visit_Slice(self, tree_node):
        self.mod_cnt += 1
        self.generic_visit(tree_node)

# Implements default mutation - replaces ast elements with syntactically correct alternatives
def mutate_default(inpt):
    inpt_ast = ast.fix_missing_locations(ast.parse(inpt))
    mvisit = MutVisit()
    mvisit.visit(inpt_ast)
    ran = 2**mvisit.mod_cnt
    reslst = []
    # Controls which percentage of operators in the condition may be mutated
    mlimit = max(floor(float(current_config["cond_mut_limit"]) * mvisit.mod_cnt), 1)
    for i in range(1, ran):
        bin_num = format(i, "b").zfill(mvisit.mod_cnt)
        if bin_num.count("1") > mlimit:
            continue
        inpt_ast = ast.fix_missing_locations(ast.parse(inpt))
        mtrans = MutTransformer(bin_num)
        res = mtrans.visit(inpt_ast)
        reslst.append((astunparse.unparse(res).lstrip().rstrip(),bin_num))
    return reslst

# Computes the "left difference" of two sets.
# This returns two sets: 
# prim(ary): the list of conditions that have a fixed value for the valid string which differs from the mutated string
# sec(ondary): the list of condition that the mutated string caused but were not relevant to the original string (either True and False or not seen at all).
def get_left_diff(d1, d2):
    prim = []
    sec = []
    for e in d1.keys():
        s1 = d1[e]
        s2 = d2.get(e)
        if s2:
            if len(s1) == 2 and len(s2) == 1:
                prim.append((e, s1.difference(s2).pop()))

            elif len(s1) == 1 and len(s2) == 1 and len(s1.intersection(s2)) == 0:
                ele = s1.pop()
                s1.add(ele)
                prim.append((e, ele))
                
        elif len(s1) == 1:
            ele = s1.pop()
            s1.add(ele)
            sec.append((e,ele))

    return (prim, sec)

# Creates all possible conditions that may adjust the path of the mutated string to be like the original string
# Parameters:
# old_cond: The old condition's line number
# file: The current mutants file path
def make_new_conditions(lineno, file):
    global manual_errs
    possible_conditions = []
    # Get the full condition string
    full_str = manual_errs.get_if_from_line(lineno, file)
    # Compute partial inversions
    for part_inv in get_partial_inversions(full_str):
        possible_conditions.append((part_inv, None))
    # Reduce the string to only the condition, i.e. "if True:" becomes "True"
    cond_str = full_str[full_str.find("if")+3:full_str.rfind(":")]
    # Get default mutations
    for (new_cond, permidx) in mutate_default(cond_str):
        nc1 = full_str[:full_str.find("if")+2] + " " + new_cond + ":"
        possible_conditions.append((str(nc1),permidx))

    return possible_conditions

# Inverts an ast node, i.e. either adds or removes a unary not
def invert_ast_node(node):
    if type(node) == ast.UnaryOp:
        return node.operand
    else:
        new_node = ast.UnaryOp()
        new_node.op = ast.Not()
        new_node.operand = node
        return new_node

# Returns a list of conditions where a part is inverted
def get_partial_inversions(condition_str):
    # Remove "(el)if" and ":"
    left_part = condition_str[:condition_str.find("if ")+3]
    cond = (condition_str[condition_str.find("if ")+3:]).rstrip()[:-1]
    inv_num = 0
    res = []
    # Count how many partial inversions exist, i.e. invertible Expr and BoolOp nodes
    for node in ast.walk(ast.fix_missing_locations(ast.parse(cond))):
        if type(node) == ast.Expr:
            inv_num += 1
        elif type(node) == ast.BoolOp:
            inv_num += len(node.values)
    tidx = 0
    # Collect the inversions
    while tidx < inv_num:
        curr_ast = ast.fix_missing_locations(ast.parse(cond))
        idx = 0
        for node in ast.walk(curr_ast):
            if type(node) == ast.Expr:
                if tidx == idx:
                    tidx += 1
                    node.value = invert_ast_node(node.value)
                    break
                idx += 1
            elif type(node) == ast.BoolOp:
                if tidx in range(idx,idx+len(node.values)):
                    tidx += 1
                    node.values[tidx-idx-1] = invert_ast_node(node.values[tidx-idx-1])
                    break
                idx += len(node.values)
        res.append(left_part + astunparse.unparse(curr_ast).strip().rstrip() + ":")
    return res

# Generate all possible new conditions from a delta (pair of primary and secondary condition differences).
def get_possible_fixes(delta, file):
    (prim, sec) = delta
    fixmap = []
    # In case there are primary candidates generate a mutant for all of them.
    if prim:
        for (lineno, state) in prim:
        	fix_list = make_new_conditions(lineno,file)
        	if fix_list:
        	    fixmap.append((fix_list, lineno, state, None))
    # Otherwise test all remaining candidates
    elif sec:
        for (lineno, state) in sec:
        	fix_list = make_new_conditions(lineno,file)
        	if fix_list:
        	    fixmap.append((fix_list, lineno, None, state))
    # Returns a list of ([possible fixes for a line], line number, pre-modification condition value)
    return fixmap

# Creates a mutant by copying the script it is derived from and applying modifications for given lines
def file_copy_replace(target, source, modifications):
    with open(target, "w", encoding="UTF-8") as trgt:
        with open(source, "r", encoding="UTF-8") as src:
            for i, line in enumerate(src):
                if modifications.get(i+1) is not None and modifications.get(i+1) != "":
                    trgt.write(modifications[i+1])
                elif modifications.get(i+1) != "":
                    trgt.write(line)

# Removes all mutants that are intermediate (i.e. we cannot tell whether they are equivalent)
# The argument completed stores all non-equivalent mutants
def cleanup(mut_dir):
    re_mutant = re.compile(r"_\d+_\d+\.py$")
    for fl in glob.glob(mut_dir + "/*.py"):
        fl = fl.replace("\\", "/")
        if re_mutant.search(fl):
            os.remove(fl)

# Removes elements that would create duplicates from prim or sec and updates hrecord if necessary
def rm_dups(prsec, history, hrecord, h_index):
    if prsec:
        primindex = 0
        while primindex < len(prsec):
            mut_set = frozenset(history + [prsec[primindex][0]])
            dup_found = False
            for his in hrecord[h_index]:
                if frozenset(his) == mut_set:
                    del prsec[primindex]
                    dup_found = True
                    break
            if not dup_found:
                hrecord[h_index].append(history.copy() + [prsec[primindex][0]])
                primindex += 1

    return prsec

# Translate the dict into a frozenset of pairs to easily check for equality
def get_frozen(argtracer_dict):
    tmp = []
    for k in argtracer_dict.keys():
        for e in argtracer_dict[k]:
            tmp.append((k,e))

    return frozenset(tmp)

def main(argv, seed=None):
    random.seed(seed)
    global current_config
    current_config = get_default_config()
    arg = argv[1]
    arg = arg.replace("\\", "/")
    ar1 = arg
    orig_file = ar1
    mut_dir = arg[arg.rfind("/")+1:arg.rfind(".")] if arg.rfind("/") >= 0 else arg[:arg.rfind(".")]
    script_name = mut_dir
    mut_dir = (current_config["default_mut_dir"]+"/").replace("//","/") + mut_dir + "/"
    # Add script's directory to path
    sys.path.insert(0, mut_dir)
    # Store the reason why the mutation was completed
    mutants_with_cause = []
    # Timeout since our modifications may cause infinite loops
    timeout = int(current_config["min_timeout"]) if len(argv) < 4 or not argv[3] else argv[3]
    if not os.path.exists(mut_dir):
        os.makedirs(mut_dir)
    else:
        cleanup(mut_dir)

    # Index of the string currently processed
    str_cnt = 0
    # Mutation counter
    mut_cnt = 0
    pick_file = argv[2] if len(argv) > 2 else current_config["default_rejected"]
    pick_handle = open(pick_file, 'rb')
    rej_strs = pickle.load(pick_handle)

    # Precompute the locations of conditions and the lines of their then and else case and format the file properly
    global manual_errs
    manual_errs = argtracer.compute_base_ast(ar1, mut_dir + script_name + ".py")
    ar1 = mut_dir + script_name + ".py"

    # Record how long the slowest execution takes to have a better prediction of the required timeout
    slowest_run = 0
    # Get base values from the non-crashing run with the most conditions traversed
    progress = 1
    base_conds = []
    ln_cond = -1
    for cand in rej_strs:
        pos = 0
        print("Mutated string:", repr(cand[0]), flush=True)
        print("Valid string:", repr(cand[1]), flush=True)
        base_index = 0
        for str_inpt in cand:
            start_time = timer()
            try:
                print("Tracing:", progress, "/", 2*len(rej_strs), flush=True)
                (_,base_cond,_,someerror) = argtracer.trace(ar1, str_inpt)
                if pos == 1:
                    base_conds.append(base_cond)
                    if len(base_cond) > ln_cond:
                        basein = cand[1]
                        base_pos = base_index
                        ln_cond = len(base_cond)
                    if someerror:
                        raise SystemExit("Invalid input: " + repr(str_inpt) + ".\nAborted.")
                    base_index += 1
            finally:
                pos += 1
                time_elapsed = timer() - start_time
                if time_elapsed > slowest_run:
                    slowest_run = time_elapsed
                progress += 1
    # Choose a timeout that is very likely to let valid mutants finish
    timeout = max(timeout, int(int(current_config["timeout_slow_multi"])*slowest_run)+1)
    try:
        (_, b_cdict, _, err) = argtracer.trace(ar1, basein, timeout=timeout)
    except Timeout:
        print("Execution timed out on basestring! Try increasing timeout (currently", timeout," seconds)")    

    if err:
    	raise SystemExit("Exiting: " + pick_file + " contains no valid inputs for " + ar1)

    # Remove duplicates (same condition trace) from valid inputs
    idxl = 0
    idxr = 0
    while idxl < len(base_conds):
        idxr = idxl+1
        while idxr < len(base_conds):
            if get_frozen(base_conds[idxl]) == get_frozen(base_conds[idxr]):
                del base_conds[idxr]
            else:
                idxr += 1
        idxl += 1

    print("Amount of unique base strings:", len(base_conds), flush=True)

    print("Used baseinput:", repr(basein))

    all_generated = { int_key : [] for int_key in range(len(base_conds)) }

    # Run the mutation process for every rejected string
    for s in rej_strs:
        s = s[0]
        if int(current_config["variable_base"]) == 0:
            queue = [(ar1, [], 0, None, None, None, base_index)]
        else:
            queue = []
            for base_index in range(len(base_conds)):
                queue.append((ar1, [], 0, None, None, None, base_index))
        discarded = set()
        # Save which exception the first execution of the rejected string produced
        original_ex_str = None
        while queue:
            (arg, history, retries, pidx, pmstate, scstate, b_cindex) = queue.pop(0)
            b_cdict = base_conds[b_cindex]
            print("Current script:", arg, flush=True)
            # Check whether the chosen correct string is now rejected
            try:
                _mod = imp.load_source('mymod', arg)
            except:
                print("Discarded script:", arg, "(import error)", flush=True)
                os.remove(arg)
                continue
            print("Executing basestring...", flush=True)
            try:
                (lines, _, _, berr) = argtracer.trace(arg, basein, timeout=timeout)
            except argtracer.Timeout:
                print("Discarding:", arg, "(basestring timed out)", flush=True)
                os.remove(arg)
                continue

            # Remove lines used to construct custom exceptions
            lines = manual_errs.remove_custom_lines(lines)

            # If the crash happens on a condition we modified there is a high chance it's invalid, so we remove it.
            if lines[0] in history:
                print("Removed:", arg, "(potentially corrupted condition)", flush=True)
                os.remove(arg)
                continue

            # Mutation guided by rejected strings

            try:
                (lines, cdict, _, err) = argtracer.trace(arg, s, timeout=timeout)
            except:
            	print("Tracer timed out on mutated string", flush=True)
            	os.remove(arg)
            	continue

            # Remove lines used to construct custom exceptions
            lines = manual_errs.remove_custom_lines(lines)
            # If the crash happens on a condition we modified there is a high chance it's invalid, so we remove it.
            if lines[0] in history:
                print("Removed:", arg, "(potentially corrupted condition)", flush=True)
                os.remove(arg)
                continue

            if original_ex_str is None:
                if err == False:
                    print("Skipping string:", s, "(not rejected)!", flush=True)
                    continue
                else:
                    original_ex_str = str(err.__class__)

            # Check whether the modification changed the condition state
            skip = (pmstate is not None and cdict.get(history[-1]) is not None and cdict.get(history[-1]) == pmstate)

            if skip:
                print("Removed:", arg, "(unsuccessful modification)", flush=True)
                if retries < int(current_config["mut_retries"]) and pidx:
                    # Try again
                    full_str = manual_errs.get_if_from_line(history[-1], arg)
                    cond_str = full_str[full_str.find("if")+3:full_str.rfind(":")]
                    inpt_ast = ast.fix_missing_locations(ast.parse(cond_str))
                    mvisit = MutVisit()
                    mvisit.visit(inpt_ast)
                    # The previous modification changed the amount of tokens.
                    if mvisit.mod_cnt > len(pidx):
                        pidx = pidx.zfill(mvisit.mod_cnt)
                    mtrans = MutTransformer(pidx)
                    res = mtrans.visit(inpt_ast)
                    fix = full_str[:full_str.find("if")+2] + " " + astunparse.unparse(res).lstrip().rstrip() + ":"
                    if not fix.endswith("\n"):
                        fix = fix + "\n"
                        mods = { history[-1] : fix }
                        cand = mut_dir + script_name + "_" + str(str_cnt) + "_" + str(mut_cnt) + ".py"
                        queue.insert(0,(cand, history.copy(), retries+1, pidx, pstate, None, b_cindex))
                        file_copy_replace(cand, arg, mods)
                        mut_cnt += 1
                elif retries >= int(current_config["mut_retries"]):
                    print("Retries exceeded:", arg, flush=True)
                os.remove(arg)
                continue

            sskip = (scstate is not None and cdict.get(history[-1]) is not None and cdict.get(history[-1]) == scstate)
            # Retries would be possible here as well, but since our search is blind for these conditions it's skipped
            if sskip:
                print("Removed:", arg, "(unsuccessful modification) (sec)", flush=True)
                os.remove(arg)
                continue

            if berr:
                print("Mutation complete:", arg, "(base rejected)", flush=True)
                print("Exception for base on", arg, ":", repr(berr), flush=True)
                mutants_with_cause.append((arg, "valid string rejected"))

            (prim, sec) = get_left_diff(cdict, b_cdict)
            # Remove all elements that have been explored (history) or do not belong to the actual code (i.e. error constructor - lines)
            prim = [e for e in prim if e[0] not in history and e[0] in lines]
            sec = [e for e in sec if e[0] not in history and e[0] in lines] if int(current_config["blind_continue"]) else []
           
            # Don't create mutants if their line combination is already in the queue
            prim = [] if not prim else rm_dups(prim, history, all_generated, b_cindex)

            # Sec will never be progressed if prim is not empty
            sec = [] if not sec or len(prim) > 0 else rm_dups(sec, history, all_generated, b_cindex)

            print("Used string:", repr(s), flush=True)
            print("Queue length:", len(queue), flush=True)
            print("Change history:", history, flush=True)
            print("Difference to base (flipped):", prim, flush=True)
            print("Difference to base (new):", sec, flush=True)
            print("Final line:", str(lines[0]), flush=True)
            print("", flush=True)
            if err:
            	# Check whether the exception is different from the first encountered one
            	diff_err = str(err.__class__) != original_ex_str
            	err = True
            print("Mutated string rejected:", err, "different:", diff_err, flush=True)
            if (err and not diff_err) or int(current_config["early_stop"]) == 0:
                all_fixes = get_possible_fixes((prim, sec), arg)
                if all_fixes:
                    for (fix_list, fix_line, pstate, sstate) in all_fixes:
                        # Create a mutant for every possible fix
                        for (fix, permindex) in fix_list:
                            if not fix.endswith("\n"):
                                fix = fix + "\n"
                            cand = mut_dir + script_name + "_" + str(str_cnt) + "_" + str(mut_cnt) + ".py"
                            mods = { fix_line : fix }
                            queue.insert(0,(cand, history.copy()+[fix_line],0, permindex, pstate, sstate, b_cindex))
                            file_copy_replace(cand, arg, mods)
                            mut_cnt += 1
            # Check whether the mutant is valid (rejects base or accepts mutated string) and record its behaviour
            if arg != ar1:
                if not err or diff_err:
                	print("Mutation complete:", arg, "(mutated string accepted)", flush=True)
                	mutants_with_cause.append((arg, "mutated string accepted"))
                elif not berr:
                    discarded.add(arg)
            		
        # Don't delete the original script, we need it to create mutants from whenever a new rejected string is processed
        discarded.discard(ar1)
        # Remove all scripts that neither reject the base string nor accept the mutated string
        for scrpt in discarded:
            print("Removed:", scrpt, flush=True)
            os.remove(scrpt)
        # Adjust the file naming
        str_cnt += 1
        mut_cnt = 0
        print("Processing string number:", str(str_cnt), "/", str(len(rej_strs)),flush=True)
    # Move the copy of the original script since it is not a mutant
    if not os.path.exists(mut_dir+"original/"):
        os.makedirs(mut_dir+"original/")

    os.rename(ar1, ar1[:ar1.rfind("/")] + "/original"+ar1[ar1.rfind("/"):])
    print("Done. The final mutants are in:", mut_dir)
    # Write a log on why each file was kept. This way we (or check_results.py) can check whether the mutation procedure is working correctly.
    with open(mut_dir[:-1] + "_inputs.log", "w", encoding="UTF-8") as file:
            for i in range(len(rej_strs)):
                file.write(str(i) + ": " + repr(rej_strs[i][0])+"\n")
            file.write("The baseinput was: " + repr(basein))

    mutants_with_cause = remove_duplicates(mut_dir, ".py", mutants_with_cause)

    with open(mut_dir[:-1] + ".log", "w", encoding="UTF-8") as file:
        file.write("Mutating script: " + repr(orig_file) + "\n")
        for e in mutants_with_cause:
            file.write(repr(e) + "\n")

# Reads a file and returns both its content and the content's hash using a cache. Used for finding straight duplicate mutant files.
@functools.lru_cache(maxsize=None)
def read_file_hashed(filename):
    with open(filename, "r", encoding="UTF-8") as fli:
        res = fli.read()
        return (res,hash(res))

# Simple duplicate removal method - given a file directory (mutation results), a file extension (.py) as well as the list of mutant, cause pairs
# Removes all duplicates (i.e. same content) from both the file-system and the list of pairs
def remove_duplicates(fdir, ext, pairlst):
    print("Removing duplicates...", flush=True)
    ext = ext if not ext.startswith(".") else ext[1:]
    fdir = fdir if not fdir.endswith("/") else fdir[:-1]
    files = []
    dups = []
    rmdup = []
    for fl in glob.glob(fdir + "/*." + ext):
        fl = fl.replace("\\", "/")
        files.append(fl)

    if len(files) < 2:
        return pairlst
    cmps = (len(files)*(len(files)-1))/2
    lstep = 0
    prog = 0

    for idx1 in range(len(files)):
        fl1 = files[idx1]
        s1 = read_file_hashed(fl1)
        for idx2 in range(idx1+1,len(files)):
            fl2 = files[idx2]
            s2 = read_file_hashed(fl2)
            if s1[1] == s2[1] and s1[0] == s2[0]:
                dups.append((fl1, fl2))
            prog += 1
            cprog = (prog/cmps)*100
            if cprog > lstep:
                lstep += 1
                print("Progress:", int(cprog), "%", flush=True)

    for (a, b) in dups:
        if os.path.exists(a) and os.path.exists(b):
            os.remove(b)
            rmdup.append(b)

    i = 0
    while i < len(pairlst):
        if pairlst[i][0] in rmdup:
            del pairlst[i]
        else:
            i += 1

    print("Removed duplicates:", len(rmdup), flush=True)

    return pairlst


if __name__ == "__main__":
    main(sys.argv)