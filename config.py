#!/usr/bin/env python3
def get_default_config(conf_path=None):
	if conf_path:
	    with open(conf_path, "r", encoding="UTF-8") as conf:
	        return eval(conf.read())
	else:
		# This dict contains the standard config of MAURIS, i.e. every tunable variable
		# All mappings are string -> string
		DEFAULT_CONFIG = {
		# The minimal timeout for each script execution in s
		"min_timeout" : "1",
		# Timeout for the unittest execution in s
		"unittest_timeout" : "5",
		# Overhead for the generation time limit
		"best_overhead" : "0.9",
		# Default Time limit for the generation algorithm in s
		"default_gen_time" : "900",
		# Default binary output file for rejected strings
		"default_rejected" : "rejected.bin",
		# Maximum attempts of how often a valid string gets mutated to get an invalid string
		"max_mut_attempts" : "10000",
		# The type of arguments to trace. taintedstr.tstr is recommended for accuracy, using str may help compatibility.
		"trace_type" : "''",
		#"trace_type" : "taintedstr.tstr('')",
		# Default folder where mutation results are stored. There may be a fair bit of stress put on the drive.
		"default_mut_dir" : "mutants/",
		# The timeout from the actual script execution is calculated as int(multi*(slowest seen execution)) + 1. Multi can be adjusted here (default is 2).
		"timeout_slow_multi" : "2",
		# Remove potentially invalid scripts after checking? Only applies when running check_results directly.
		"default_clean_invalid" : "0",
		# Percentage of elements in a condition that may be mutated. Setting this to 0 will still allow 1 mutation per condition.
		"cond_mut_limit" : "1.0",
		# Number of retries for mutating a condition
		"mut_retries" : "10",
		# Indicates whether the mutation algorithm should: always use the most complex string ("0"), or use a combination of all ("1")
		"variable_base" : "1",
		# Set to 0 to disallow blind modifications whenever there are no guided ones. This reduces the required time and space (drive and memory) significantly, but the results may be worse.
		"blind_continue" : "1",
		}
		return DEFAULT_CONFIG