#!/usr/bin/env python3
import sys
from config import get_default_config
import glob
import re
import os
import shutil

def clone_and_replace(scrpt, base_dir, sub_dir, orig_script):
	if os.path.isdir(scrpt[:-3]):
		shutil.rmtree(scrpt[:-3])
	shutil.copytree(base_dir, scrpt[:-3])
	os.remove(scrpt[:-3] + "/" + sub_dir + orig_script)
	shutil.copy(scrpt, scrpt[:-3] + "/" + sub_dir + orig_script)
	os.remove(scrpt)

def split_path_at_base(path, base):
	idx = 0
	for i in range(min(len(path),len(base))):
		if path[idx] != base[idx]:
			break
		else:
			idx += 1
	path = path[idx:]
	if path.find("/") >= 0:
		r1 = path[:path.find("/")+1]
		r2 = path[path.find("/")+1:]
	else:
		r1 = ""
		r2 = path
	return (r1, r2)

def main(args):
	if len(args) < 3:
		raise SystemExit("Please specify a script path and its project directory")
	current_config = get_default_config()
	script = args[1] if not args[1].endswith(".py") else args[1][:-3]
	script = script.replace("\\","/")
	base_dir = args[2]
	(sub_dir, script) = split_path_at_base(script,base_dir)
	re_mutant = re.compile((current_config["default_mut_dir"] + "/").replace("//","/") + script + "/" + script + "_\d+_\d+.py$")
	for scrpt in glob.glob((current_config["default_mut_dir"] + "/").replace("//", "/") + script + "/*.py"):
		if os.path.isfile(scrpt):
			scrpt = scrpt.replace("\\","/")
			if re_mutant.search(scrpt):
				clone_and_replace(scrpt, base_dir, sub_dir, script + ".py")

if __name__ == "__main__":
	main(sys.argv)