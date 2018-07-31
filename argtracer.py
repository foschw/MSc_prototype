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

cond_dict = {}
lines = []
vrs = {}
ar = ""
timeo = None
time_start = None
# target_type = type("")
# By using the commented line instead we get a seizable improvement in execution time but may consume more memory
target_type = type(taintedstr.tstr(''))
base_ast = None
cond_flag = False

class RaiseAndCondAST:
	def __init__(self, sourcefile, deformattedfile):
		self.source = sourcefile
		self.myast = ast.parse(RaiseAndCondAST.expr_from_source(sourcefile), sourcefile)
		ast.fix_missing_locations(self.myast)
		with open(deformattedfile,"w", encoding="UTF-8") as defile:
			defile.write(astunparse.unparse(self.myast))
		self.myast = ast.parse(RaiseAndCondAST.expr_from_source(deformattedfile), deformattedfile)
		ast.fix_missing_locations(self.myast)
		self.exc_lines = []
		self.cond_dict = {}
		self.compute_lines()		

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

	def is_exception_line(self, lineno):
		return lineno in self.exc_lines

	def is_condition_line(self, lineno):
		return self.cond_dict.get(lineno) is not None

	def print_exception_lines(self):
		print(self.exc_lines)

	def print_cond_lines(self):
		print(self.cond_dict.keys())

	def expr_from_source(source):
		expr = ""
		with open(source, "r", encoding="UTF-8") as file:
			expr = file.read()
		return expr

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

class Timeout(Exception):
    pass

def compute_base_ast(sourcefile, defile):
	global base_ast
	base_ast = RaiseAndCondAST(sourcefile, defile)
	return base_ast

def line_tracer(frame, event, arg):
	if event == 'line':
		global lines
		global fl
		global ar
		global timeo
		global time_start
		global cond_dict
		global target_type
		global base_ast
		global cond_flag
		if fl in frame.f_code.co_filename:
			if timeo:
				end = timer()
				if (end - time_start) >= timeo:
					raise Timeout("Execution timed out!")
			if cond_flag:
				bval = base_ast.cond_dict[lines[0]] == frame.f_lineno
				if cond_dict.get(lines[0]): 
					cond_dict[lines[0]].add(bval)
				else:
					cond_set = set()
					cond_set.add(bval)
					cond_dict[lines[0]] = cond_set
				cond_flag = False
			lines.insert(0, frame.f_lineno)
			if base_ast.is_condition_line(frame.f_lineno): 
				cond_flag = True
				global vrs
				vass = vrs.get(frame.f_lineno) if vrs.get(frame.f_lineno) else []
				avail = [v for v in vass[0]] if vass else None
				for var in frame.f_locals.keys():
					val = frame.f_locals[var]
					if type(val) == target_type:
						if not avail or var in avail and (var,str(val)) not in vass:
							vass.append((var, str(val)))
				vrs[frame.f_lineno] = vass

	return line_tracer

def trace(arg, inpt, timeout=None):
    global lines
    global vrs
    global ar
    global timeo
    global time_start
    global cond_dict
    global cond_flag
    if timeout:
        time_start = timer()
        timeo = timeout
    else:
        timeo = None
        time_start = None
    ar = arg
    lines = []
    vrs = {}
    cond_dict = {}
    err = False
    cond_flag = False
    # Automatically adjust to target type
    inpt = target_type(inpt)
    _mod = imp.load_source('mymod', arg)
    global fl
    fl = arg.replace("\\", "/")
    fl = arg[arg.index("/"):] if arg.startswith(".") else arg
    fl = fl[:arg.rindex("/")-1] if arg.rfind("/") != -1 else fl
    try:
        sys.settrace(line_tracer)
        res = _mod.main(inpt)
    except Timeout:
        sys.settrace(None)
        raise
    except Exception as ex:
    	err = ex
    	sys.settrace(None)
    	traceback.print_exc()
    sys.settrace(None)
    return (lines.copy(), cond_dict.copy(), vrs.copy(), err)
