#!/usr/bin/env python3
import sys
import subprocess
import re
import os
import glob
from config import get_default_config

current_config = None

# Executes the test suite of a .py file
# Returns the amount of tests passed and failed as a pair
def run_unittests_for_script(script):
	cmd = ["python", "-m", "unittest", script[script.rfind("/")+1:]]
	script_dir = os.path.abspath(script[:script.rfind("/")+1]).replace("\\","/")
	try:
		proc = subprocess.Popen(cmd, shell=False,stderr=subprocess.PIPE,cwd=script_dir)
		res = proc.communicate()[1].decode(sys.stderr.encoding)
	except:
		raise SystemExit("Unittest execution failed.")
	return extract_test_stats(res)

# Extracts the amount of test passes p and fails f as pair (p, f)
def extract_test_stats(unittest_output):
	outpt_lines = unittest_output.split("\n")
	re_test_num = r"^Ran \d+ test(s)? in \d(\.)?\d*s"
	re_test_fails = r"^FAILED \(((failures(=\d+)?)?(, )?(errors)?)=\d+\)"
	total_tests = 0
	res_open = False
	for l in outpt_lines:
		l = l.lstrip().rstrip()
		if re.match(re_test_num, l):
			total_tests = int(l[4:l.find("test")])
			res_open = True
		elif (l == "OK") and res_open:
			num_fail = 0
		elif re.match(re_test_fails,l) and res_open:
			re_num = re.compile("=\d+")
			num_fail = 0
			for ob in re_num.findall(l):
				num_fail += int(ob[1:])
	return (total_tests-num_fail,num_fail)

def main(argv):
	current_config = get_default_config()
	# Specify the original name of the script or its path to check the results. 
	if len(argv) < 2:
		raise SystemExit("Please specify the script name!")

	scriptname = argv[1] if not argv[1].endswith(".py") else argv[1][:argv[1].rfind(".py")]
	if scriptname.rfind("/"):
		scriptname = scriptname[scriptname.rfind("/")+1:]
	mut_pattern = (current_config["default_mut_dir"]+"/").replace("//","/") + scriptname + "/*.py"
	test_res_fl = (current_config["default_mut_dir"]+"/").replace("//","/") + scriptname + "_test_results.log"
	scripts_f = []
	scripts_p = []
	for f in glob.glob(mut_pattern):
		if os.path.isfile(f):
			f = f.replace("\\","/")
			print("Running tests for: " + f, flush=True)
			(tpass,tfail) = run_unittests_for_script(f)
			if tfail == 0:
				scripts_p.append((f,run_unittests_for_script(f)))
			else:
				scripts_f.append((f,run_unittests_for_script(f)))

	# Write the test stats to a file. Mutants that fail no tests are at the top if they exist.
	with open(test_res_fl, "w", encoding="UTF-8") as dest:
		for (scrpt, (tpass,tfail)) in scripts_p:
			dest.write(scrpt + ":\nPass: " + str(tpass) + ", Fail: " + str(tfail) + " \n")
			dest.write("\n")

		if scripts_p and scripts_f:
			dest.write("---------------------------------------------------------------------------------------------------\n")
			dest.write("\n")

		for (scrpt, (tpass,tfail)) in scripts_f:
			dest.write(scrpt + ":\nPass: " + str(tpass) + ", Fail: " + str(tfail) + " \n")
			dest.write("\n")

if __name__ == "__main__":
	main(sys.argv)