#!/usr/bin/env python3
import imp
import sys
import traceback
import taintedstr
import re
import functools
from timeit import default_timer as timer
import ast
import astunparse
from config import get_default_config

# Maps a condition line to the line of its then branch
cond_dict = {}
# Records all lines the program executed
lines = []
# Maps a variable to all its recorded assignments
vrs = {}
# TODO
ar = ""
# Timeout value
timeo = None
# The time the execution started. Used to abort in case a timeout occurs.
time_start = None
# target_type = type("")
# By using the commented line instead we get a seizable improvement in execution time but may consume more memory
target_type = eval("type("+get_default_config()["trace_type"]+")")
# The AST of the original file. Stores where exceptions are manually raised and line numbers of conditional branches
base_ast = None
# Indicates which condition needs to be resolved at which call depth (call and return). 
# This way we know whether a condition is True or False without directly evaluating.
cond_flag = {}
# The current call depth
depth = -1

# The AST that stores where exceptions are raised as well as the condition to then branch mapping-
class RaiseAndCondAST:
	def __init__(self, sourcefile, deformattedfile):
		# Get the program's AST
		self.source = sourcefile
		self.myast = ast.parse(RaiseAndCondAST.expr_from_source(sourcefile), sourcefile)
		ast.fix_missing_locations(self.myast)
		# Use ASTUnparse to get uniform formatting
		with open(deformattedfile,"w", encoding="UTF-8") as defile:
			defile.write(astunparse.unparse(self.myast))
		self.myast = ast.parse(RaiseAndCondAST.expr_from_source(deformattedfile), deformattedfile)
		ast.fix_missing_locations(self.myast)
		# Stores where raise statements are located
		self.exc_lines = []
		# Stores for each condition line the line of its then branch
		self.cond_dict = {}
		self.compute_lines()		

	# Find all lines that contain raise statements as well as conditional mappings
	def compute_lines(self):
		for stmnt in ast.walk(self.myast):
			if isinstance(stmnt, ast.If):
				startline = stmnt.lineno
				endline = stmnt.body[0].lineno
				if not self.cond_dict.get(startline):
					self.cond_dict[startline] = endline
			elif isinstance(stmnt, ast.Raise):
				for sm in ast.walk(stmnt):
					if hasattr(sm, "lineno") and sm.lineno not in self.exc_lines:
						self.exc_lines.append(sm.lineno)

	# Checks whether a given line manually raises an exception
	def is_exception_line(self, lineno):
		return lineno in self.exc_lines

	# Checks whether a given line contains a conditional statement
	def is_condition_line(self, lineno):
		return self.cond_dict.get(lineno) is not None

	# Prints all exception line locations
	def print_exception_lines(self):
		print(self.exc_lines)

	# Prints all conditional line locations
	def print_cond_lines(self):
		print(self.cond_dict.keys())

	# Loads a file for ast.parse
	def expr_from_source(source):
		expr = ""
		with open(source, "r", encoding="UTF-8") as file:
			expr = file.read()
		return expr

	# Retrieves the conditional statement from the file
	def get_if_from_line(self, line_num, target_file):
		if not self.is_condition_line(line_num): return None
		else:
			cond = ""
			with open(target_file, "r", encoding="UTF-8") as fp:
				for i, line in enumerate(fp):
					if i+1 == line_num:
						cond = line
						break
		return cond

# Raised in case the execution times out
class Timeout(Exception):
    pass

# Computes the AST for the sourcefile and sets it globally
def compute_base_ast(sourcefile, defile):
	global base_ast
	base_ast = RaiseAndCondAST(sourcefile, defile)
	return base_ast

def line_tracer(frame, event, arg):
	global fl
	if fl in frame.f_code.co_filename:
		# Manage the call depth
		global depth
		if event == 'call':
			depth += 1
		elif event == 'return':
			depth -= 1
		if event == 'line':
			global lines
			global ar
			global timeo
			global time_start
			global cond_dict
			global target_type
			global base_ast
			global cond_flag
			# Raise a timeout in case the execution takes too long
			if timeo:
				end = timer()
				if (end - time_start) >= timeo:
					raise Timeout("Execution timed out!")
			# Check whether a condition needs to be resolved at the current depth
			if cond_flag.get(depth):
				bval = base_ast.cond_dict[cond_flag[depth]] == frame.f_lineno
				# Add to the set of seen outcomes for the given line its current truth value
				if cond_dict.get(cond_flag[depth]): 
					cond_dict[cond_flag[depth]].add(bval)
				else:
					# Since a condition can be both True and False during an execution we save all truth values seen in a set
					cond_set = set()
					cond_set.add(bval)
					cond_dict[cond_flag[depth]] = cond_set
				cond_flag.pop(depth)
			# Record the current line
			lines.insert(0, frame.f_lineno)
			# Record all variable assignments for condition lines
			if base_ast.is_condition_line(frame.f_lineno): 
				cond_flag[depth] = frame.f_lineno
				global vrs
				vass = vrs.get(frame.f_lineno) if vrs.get(frame.f_lineno) else []
				# Only consider always initialized variables
				avail = [v for v in vass[0]] if vass else None
				for var in frame.f_locals.keys():
					val = frame.f_locals[var]
					if type(val) == target_type:
						if not avail or var in avail and (var,str(val)) not in vass:
							vass.append((var, str(val)))
				vrs[frame.f_lineno] = vass

	return line_tracer

def trace(arg, inpt, timeout=None):
	# Clear all global assignments
    global lines
    global vrs
    global ar
    global timeo
    global time_start
    global cond_dict
    global cond_flag
    global depth
    if timeout:
        time_start = timer()
        timeo = timeout
    else:
        timeo = None
        time_start = None
    depth = -1
    ar = arg
    lines = []
    vrs = {}
    cond_dict = {}
    err = False
    cond_flag = {}
    # Automatically adjust to target type
    inpt = target_type(inpt)
    _mod = imp.load_source('mymod', arg)
    # Stores which script is observed
    global fl
    fl = arg.replace("\\", "/")
    fl = arg[arg.index("/"):] if arg.startswith(".") else arg
    fl = fl[:arg.rindex("/")-1] if arg.rfind("/") != -1 else fl
    try:
        sys.settrace(line_tracer)
        res = _mod.main(inpt)
    except Timeout:
        sys.settrace(None)
        # If an execution encounters a timeout the script is discarded
        raise
    except Exception as ex:
    	err = ex
    	sys.settrace(None)
    	traceback.print_exc()
    sys.settrace(None)
    # Return all lines, conditional lines with their branch (True/False), all observed variable assignments and the exception encountered
    return (lines.copy(), cond_dict.copy(), vrs.copy(), err)
