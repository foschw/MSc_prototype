#!/usr/bin/env python3
import sys
import subprocess
import re
import os
from config import get_default_config
from tidydir import TidyDir as TidyDir
import concurrent.futures
import glob
from find_mutation_lines import LogWriter

current_config = None

# Executes the test suite of a .py file
# Returns the amount of tests passed and failed as a pair
def run_unittests_for_script(script):
	cmd = ["python", "-m", "unittest", script[script.rfind("/")+1:]]
	script_dir = os.path.abspath(script[:script.rfind("/")+1]).replace("\\","/")
	try:
		proc = subprocess.Popen(cmd, shell=False,stderr=subprocess.PIPE,cwd=script_dir)
		res = proc.communicate(timeout=int(current_config["unittest_timeout"]))[1].decode(sys.stderr.encoding)
	except subprocess.TimeoutExpired:
		proc.kill()
		proc.communicate()
		return (-1,-1)
	except:
		raise SystemExit("Unit test execution failed.")
	return extract_test_stats(res)

# Extracts the amount of test passes p and fails f as pair (p, f)
def extract_test_stats(unittest_output):
	outpt_lines = unittest_output.split("\n")
	re_test_num = r"^Ran \d+ test(s)? in \d(\.)?\d*s"
	re_test_fails = r"^FAILED \(((failures(=\d+)?)?(, )?(errors)?)=\d+\)"
	total_tests = 0
	res_open = False
	num_fail = -2
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
	# This requires manual examination
	if num_fail == -2:
		return (-2,-2)
	return (total_tests-num_fail,num_fail)

# Running tests can be done independently
def run_tests_threaded(script):
	return run_unittests_for_script(script)

def main(argv):
	global current_config
	current_config = get_default_config()
	# Specify the original name of the script or its path to check the results. 
	if len(argv) < 2:
		raise SystemExit("Please specify the folder the scripts are in!")
	argv[1] = argv[1].replace("\\", "/")
	argv[1] = argv[1][:-1] if argv[1].endswith("/") else argv[1]
	test_res_fl = argv[1] + "_test_results.log"
	lwriter = LogWriter(test_res_fl)
	scripts_f = []
	scripts_p = []
	targets = []
	num_workers = int(current_config["test_threads"])
	run_seq = []

	for fnm in glob.iglob(argv[1]+"/*.py", recursive=True):
		fnm = fnm.replace("\\","/")
		if fnm not in targets:
			targets.append(fnm)

	with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as tpe:
		future_to_script = {tpe.submit(run_tests_threaded, test_script) : test_script for test_script in targets}
		fidx = 0
		for future in concurrent.futures.as_completed(future_to_script):
			print("Running tests:", str(fidx+1) + "/" + str(len(targets)), flush=True)
			test_script = future_to_script[future]
			(tpass, tfail) = future.result()
			if tfail == 0:
				if tpass > 0:
					scripts_p.append((test_script,(tpass,tfail)))
			else:
				# Retry scripts that timed out in sequential mode (more robust)
				if tpass == -1 and num_workers > 1:
					run_seq.append(test_script)
				else:
					scripts_f.append((test_script,(tpass,tfail)))
			lwriter.append_line(test_script + ":\nPass: " + str(tpass) + ", Fail: " + str(tfail) + " \n" + "\n")
			fidx += 1

	if run_seq:
		print("Running", len(run_seq), "scripts in sequential mode...", flush=True)
		seqidx = 0
		for test_script in run_seq:
			print("Re-running tests:", str(seqidx+1), "/", str(len(run_seq)), flush=True)
			seqidx += 1
			(tpass, tfail) = run_unittests_for_script(test_script)
			if tfail == 0:
				if tpass > 0:
					scripts_p.append((test_script,(tpass,tfail)))
			else:
				scripts_f.append((test_script,(tpass,tfail)))


	# Write the test stats to a file. Mutants that fail no tests are at the top if they exist.
	with open(test_res_fl, "w", encoding="UTF-8") as dest:
		scripts_p = sorted(scripts_p, key=by_index)
		for (scrpt, (tpass,tfail)) in scripts_p:
			dest.write(scrpt + ":\nPass: " + str(tpass) + ", Fail: " + str(tfail) + " \n")
			dest.write("\n")

		if scripts_p and scripts_f:
			dest.write("---------------------------------------------------------------------------------------------------\n")
			dest.write("\n")

		scripts_f = sorted(sorted(scripts_f, key=by_index), key=by_fail)

		for (scrpt, (tpass,tfail)) in scripts_f:
			dest.write(scrpt + ":\nPass: " + str(tpass) + ", Fail: " + str(tfail) + " \n")
			dest.write("\n")

def by_fail(result):
	(_, (_, tfail)) = result
	rv = tfail if tfail >= 0 else float("inf")
	return rv

def by_index(result):
	(mutant_name, _) = result
	ky = re.findall(r"_\d+_\d+\.py$", mutant_name)
	if len(ky) != 1:
		return mutant_name
	ky = ky[0][1:-3]
	return (int(ky[:ky.find("_")]), int(ky[ky.find("_")+1:]))

if __name__ == "__main__":
	main(sys.argv)