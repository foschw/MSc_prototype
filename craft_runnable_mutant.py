#!/usr/bin/env python3
import sys
from config import get_default_config
import glob
import re
import os
import shutil
from tidydir import TidyDir as TidyDir

def clone_and_replace(scrpt, base_dir, sub_dir, orig_script):
	if os.path.isdir(scrpt[:-3]):
		shutil.rmtree(scrpt[:-3])
	shutil.copytree(str(base_dir), scrpt[:-3])
	os.remove(scrpt[:-3] + "/" + sub_dir + orig_script)
	shutil.copy(scrpt, scrpt[:-3] + "/" + sub_dir + orig_script)
	os.remove(scrpt)

def main(args):
	if len(args) < 3:
		raise SystemExit("Please specify a script path and its project directory")
	current_config = get_default_config()
	script = args[1] if not args[1].endswith(".py") else args[1][:-3]
	script = script.replace("\\","/")
	base_dir = TidyDir(args[2])
	(sub_dir, script) = base_dir.split_path(script)
	re_mutant = re.compile(str(TidyDir(current_config["default_mut_dir"]) + TidyDir(script,guess=False)) + script + "_\d+_\d+.py$")
	for scrpt in glob.glob(TidyDir(current_config["default_mut_dir"]) + script + "*.py"):
		if os.path.isfile(scrpt):
			scrpt = scrpt.replace("\\","/")
			if re_mutant.search(scrpt):
				clone_and_replace(scrpt, base_dir, sub_dir, script + ".py")

if __name__ == "__main__":
	main(sys.argv)