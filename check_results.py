#!/usr/bin/env python3
import sys
import subprocess
from argtracer import compute_base_ast
import re
import pickle

def execute_script_with_argument(script, argument):
	try:
		proc = subprocess.run("python " + script + " " + argument, stderr=subprocess.PIPE)
	except Exception as e:
		return e
	else:
		try:
			proc.check_returncode()
		except subprocess.CalledProcessError:
			return repr(proc.stderr)
		else:
			return None	

def main(argv):
	if len(argv) < 2:
		raise SystemExit("Please specify the script name!")

	scriptname = argv[1] if not argv[1].endswith(".py") else argv[1][:argv[1].rfind(".py")]
	if scriptname.rfind("/"):
		scriptname = scriptname[scriptname.rfind("/")+1:]
	cause_file = "mutants/" + scriptname + ".log"
	inputs_file = "rejected.bin" if len(argv) < 3 else argv[2]
	all_inputs = []
	cause_dict = {}
	base_file = None
	with open(cause_file, "r", encoding="UTF-8") as causes:
		for _, line in enumerate(causes):
			(filename, the_cause) = eval(line[:-1])
			if not base_file:
				base_file = filename
			the_cause = 0 if the_cause.find("accepted") > -1 else 1 
			the_set = [] if not cause_dict.get(filename) else cause_dict[filename]
			the_set.append(the_cause)
			cause_dict[filename] = the_set
	rej_strs = pickle.load(open(inputs_file, "rb"))
	basein = ""
	for cand in rej_strs:
		basein = cand[1] if len(cand[1]) > len(basein) else basein

	inputs = []
	for ele in rej_strs:
		inputs.append(ele[0])
	inputs.append(basein)
	base_ast = compute_base_ast(base_file, base_file)
	errs = []
	for script in cause_dict.keys():
		print("Checking script:", script)
		for the_cause in cause_dict[script]:
			# Basestring rejected
			if the_cause == 1:
				argument = inputs[-1]
				res = execute_script_with_argument(script, argument)
				if res is None:
					errs.append((script, "valid string not rejected"))
				elif type(res) != type(""):
					errs.append((script, "script execution with given argument failed"))
			# Mutated string accepted
			else:
				argument = inputs[int(script[script.find("_")+1:script.rfind("_")])]
				res = execute_script_with_argument(script, argument)
				if res is not None:
					if type(res) == type(""):
						RE_this_line = re.compile(r"File\s\"" + script + "\",\sline\s\d+,")
						err_locs = RE_this_line.findall(res)
						if err_locs:
							reject = False
							for err_loc in err_locs:
								err_loc = err_loc[err_loc.rfind(", line ")+7:err_loc.rfind(",")]
								reject = reject or base_ast.is_exception_line(int(err_loc))
							if reject:
								errs.append((script, "mutated string rejected"))
					else:
						errs.append((script, "script execution with given argument failed"))
	print()
	if not errs:
		print("No problems found.")
	else:
		print("Found", len(errs), "potential problems:")
		print(errs)

if __name__ == "__main__":
	main(sys.argv)