#!/usr/bin/env python3
import imp
import sys
import traceback
import taintedstr
import re
import functools
from timeit import default_timer as timer
import ast

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

class RaiseAndCondAST:
	def __init__(self, sourcefile):
		self.source = sourcefile
		self.myast = ast.parse(RaiseAndCondAST.expr_from_source(sourcefile), sourcefile)
		ast.fix_missing_locations(self.myast)
		self.exc_lines = []
		self.cond_lines = []
		self.cond_repr = []
		self.compute_lines()		

	def compute_lines(self):
		for stmnt in ast.walk(self.myast):
			if isinstance(stmnt, ast.If):
				startline = stmnt.lineno
				endline = stmnt.body[0].lineno
				body0_off = stmnt.body[0].col_offset
				cond_off = stmnt.test.col_offset - 1
				next = self.make_next(startline, endline, body0_off)
				self.cond_repr.append((startline, endline, cond_off, next))
				if startline not in self.cond_lines:
					self.cond_lines.append(startline)
			elif isinstance(stmnt, ast.Raise):
				for sm in ast.walk(stmnt):
					if hasattr(sm, "lineno") and sm.lineno not in self.exc_lines:
						self.exc_lines.append(sm.lineno)

	def is_exception_line(self, lineno):
		return lineno in self.exc_lines

	def is_condition_line(self, lineno):
		return lineno in self.cond_lines

	def print_exception_lines(self):
		print(self.exc_lines)

	def print_cond_lines(self):
		print(self.cond_lines)

	def make_next(self, startline, endline, body0_off):
		next_frag = ""
		with open(self.source, "r", encoding="UTF-8") as fp:
			for i, line in enumerate(fp):
				if i+1 == endline:
					next_frag = line[body0_off:]
		return next_frag

	def expr_from_source(source):
		expr = ""
		with open(source, "r", encoding="UTF-8") as file:
			expr = file.read()
		return expr

	def get_condition_from_line(self, line_num, target_file):
		if line_num not in self.cond_lines: return None
		else:
			cond = ""
			for (startline, endline, cond_off, next) in self.cond_repr:
				if startline == line_num:
					with open(target_file, "r", encoding="UTF-8") as fp:
						for i, line in enumerate(fp):
							if i+1 == startline:
								cond = cond + line[cond_off:]
							if i+1 > startline and i+1 <= endline:
								cond = cond + line
					break
		cond = cond[:cond.rfind(next)]
		cond = cond[:cond.rfind(":")]
		return cond

	def get_if_and_range_for_line(self, line_num, target_file):
		if line_num not in self.cond_lines: return None
		else:
			cond = ""
			for (startline, endline, offset, _) in self.cond_repr:
				if startline == line_num:
					with open(target_file, "r", encoding="UTF-8") as fp:
						for i, line in enumerate(fp):
							if i+1 >= startline and i+1 <= endline:
								cond = cond + line
					break
		return (cond, startline, endline, offset)


class Timeout(Exception):
    pass

def compute_base_ast(sourcefile):
	global base_ast
	base_ast = RaiseAndCondAST(sourcefile)
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
        if fl in frame.f_code.co_filename:
            if timeo:
                end = timer()
                if (end - time_start) >= timeo:
                    raise Timeout("Execution timed out!")
            lines.insert(0, frame.f_lineno)
            if base_ast.is_condition_line(frame.f_lineno):
                cond = base_ast.get_condition_from_line(frame.f_lineno, ar)
                try:
                	# NOTE: This will break the execution in case the condition causes sideffects like modifying an object
                	# To prevent this we may implement a less aggressive mode, which deep copies all variables the condition modifies in both globals and locals if needed
                    bval = eval(cond, frame.f_globals, frame.f_locals)
                    # Make bval boolean to take care of e.g. if var etc.
                    if bval:
                    	bval = True
                    else:
                    	bval = False
                    if cond_dict.get(frame.f_lineno):
                        cond_dict[frame.f_lineno].add(bval)
                    else:
                        cond_set = set()
                        cond_set.add(bval)
                        cond_dict[frame.f_lineno] = cond_set
                except:
                    # This is not a good idea, but better than crashing for now
                    print("WARNING: unable to infer condition result in line:", frame.f_lineno)
                    pass
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
