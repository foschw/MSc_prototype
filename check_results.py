#!/usr/bin/env python3
import sys
import subprocess
import re
import pickle
import os

# Executes a .py file with a string argument.
# Returns the exception in case a problem occured, None otherwise.
def execute_script_with_argument(script, argument):
	cmd = ["python", script, argument]
	try:
		proc = subprocess.Popen(cmd, shell=True,stderr=subprocess.PIPE)
		err = proc.communicate()[1].decode(sys.stderr.encoding)
	except:
		return "-1"
	return extract_error_name(err)

# Extracts the error name from a traceback string
def extract_error_name(stderr_string):
	exc_name = None
	if not stderr_string:
		return exc_name

	if stderr_string.find("Traceback (most recent call last):") < 0:
		return "-1"
	
	err_arr = stderr_string.split("\n")
	skip_next = False
	started = False
	re_skipnext = re.compile(r'\s*File "')
	for errmsg in err_arr:
		if len(errmsg) > 1:
			if not started:
				started = True
			elif skip_next:
				skip_next = False
			elif re.match(re_skipnext, errmsg):
				skip_next = True
			elif errmsg.find(":") > 0:
				exc_name = errmsg.lstrip()
				break

	exc_name = exc_name[:exc_name.find(":")]
	return exc_name


# Removes potentially invalid mutants based on the error list and fixes the log accordingly
def clean_and_fix_log(errs, behave, logfile):
	tmp = logfile + "_"
	with open(tmp, "w", encoding="UTF-8") as dest:
		with open(logfile, "r", encoding="UTF-8") as log:
			for num, line in enumerate(log):
				if num == 0:
					dest.write(line)
				else:
					scrpt, cause = eval(line)
					if not errs.get(scrpt) or cause.replace("string", "string not") not in errs.get(scrpt):
						dest.write(line)

	for fl in errs:
		if not behave.get(fl):
			os.remove(fl)

	os.remove(logfile)
	os.rename(tmp, logfile)

def main(argv):
	# Specify the original name of the script to check the results. 
	# Uses the second argument as binary input file, or "rejected.bin" in case it is ommitted.
	# The optional third argument controls whether the unverifiable scripts are to be removed.
	if len(argv) < 2:
		raise SystemExit("Please specify the script name!")

	scriptname = argv[1] if not argv[1].endswith(".py") else argv[1][:argv[1].rfind(".py")]
	if scriptname.rfind("/"):
		scriptname = scriptname[scriptname.rfind("/")+1:]
	cause_file = "mutants/" + scriptname + ".log"
	inputs_file = "rejected.bin" if len(argv) < 3 else argv[2]
	clean_invalid = False if len(argv) < 4 else argv[3]
	all_inputs = []
	all_mutants = []
	behave = {}
	mutant_to_cause = {}

	with open(cause_file, "r", encoding="UTF-8") as causes:
		for num, line in enumerate(causes):
			# Get the path to the original script
			if num == 0:
				original_file = line.strip()
				original_file = original_file[original_file.find(":")+3:-1]
			else:
				# Use eval to get the pair representation of the line. The first element is the mutant.
				the_mutant = eval(line)[0]
				effect_set = mutant_to_cause.get(the_mutant) if mutant_to_cause.get(the_mutant) else set()
				# Code mutant behaviour as integer for easy comparison
				if eval(line)[1].find("rejected") > -1:
					effect_set.add(0)
				else:
					effect_set.add(1)
				mutant_to_cause[the_mutant] = effect_set
				if the_mutant not in all_mutants:
					all_mutants.append(the_mutant)

	rej_strs = pickle.load(open(inputs_file, "rb"))
	basein = ""
	inputs = []
	# Find the used base candidate (i.e. longest string)
	for cand in rej_strs:
		basein = str(cand[1]) if len(str(cand[1])) > len(basein) else basein
		inputs.append(str(cand[0]))

	errs = {}

	# Check whether the used valid string is actually valid
	exc_orig = execute_script_with_argument(original_file, basein)
	if exc_orig:
		raise SystemExit("Original script rejects baseinput: " + repr(basein))

	# Check all mutants for behaviour changes
	for my_mutant in all_mutants:
		print("Checking mutant:", my_mutant)
		# Check whether the valid string is rejected
		exc_mutant_valid = execute_script_with_argument(my_mutant, basein)
		if exc_mutant_valid and exc_mutant_valid != "-1":
			bh = behave.get(my_mutant) if behave.get(my_mutant) else []
			bh.append("valid string rejected")
			behave[my_mutant] = bh
		my_input = my_mutant[:my_mutant.rfind("_")]
		my_input = inputs[int(my_input[my_input.rfind("_")+1:])]
		# Check the output of the original script for the rejected string
		exc_orig_invalid = execute_script_with_argument(original_file, my_input)
		# Check the output of the mutated script for the rejected string
		exc_mutant = execute_script_with_argument(my_mutant, my_input)
		if not exc_mutant or exc_mutant == "-1":
			bh = behave.get(my_mutant) if behave.get(my_mutant) else []
			bh.append("invalid string accepted")
			behave[my_mutant] = bh
		elif exc_orig_invalid != exc_mutant and exc_mutant != "-1" and exc_orig_invalid != "-1":
			bh = behave.get(my_mutant) if behave.get(my_mutant) else []
			bh.append("invalid string raises new exception")
			behave[my_mutant] = bh

		# Compare expected and actual behaviour
		for e in mutant_to_cause.get(my_mutant):
			if e == 0 and not exc_mutant_valid or exc_mutant_valid == "-1":
				er = errs.get(my_mutant) if errs.get(my_mutant) else []
				er.append("valid string not rejected")
				errs[my_mutant] = er
			elif e == 1 and exc_mutant and exc_mutant != "-1" and exc_orig_invalid == exc_mutant:
				er = errs.get(my_mutant) if errs.get(my_mutant) else []
				er.append("mutated string not accepted")
				errs[my_mutant] = er

	print()
	if not errs:
		print("No problems found.")
	else:
		print("Found", len(errs), "potential problem(s):")
		print(errs)

	if clean_invalid:
		print()
		print("Removing potentially invalid scripts...")
		clean_and_fix_log(errs, behave, cause_file)

	print()
	print("Detected behaviour:")
	print(behave)
	for mut in behave:
		if mut[1].find("accepted") >= 0:
			print()
			print("Rare mutant:", mut)

if __name__ == "__main__":
	main(sys.argv)