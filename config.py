#!/usr/bin/env python3
def get_default_config(conf_path=None):
	if conf_path:
	    with open(conf_path, "r", encoding="UTF-8") as conf:
	        return eval(conf.read())
	else:
		# This dict contains the standard config of MAURIS, i.e. every tuneable variable
		# All mappings are string -> string
		DEFAULT_CONFIG = {
		# The minimal timeout for each script execution in s
		"min_timeout" : "1",
		# Overhead for the generation time limit
		"best_overhead" : "0.9",
		# Default Time limit for the generation algorithm in s
		"default_gen_time" : "60",
		# Default binary output file for rejected strings
		"default_rejected" : "rejected.bin",
		# Minimal length required for shrinking mutations to be applicable
		"min_mut_len" : "5",
		# Maximum attempts of how often a valid string gets mutated to get an invalid string
		"max_mut_attempts" : "100",
		# The type of arguments to trace. taintedstr.tstr is recommended for accuracy, using str may help compatibility.
		"trace_type" : "''",
		#"trace_type" : "taintedstr.tstr('')",
		# Default folder where mutation results are stored
		"default_mut_dir" : "mutants/",
		# The timeout from the actual script execution is calcualted as int(multi*(slowest seen execution)) + 1. Multi can be adjusted here (default is 2).
		"timeout_slow_multi" : "2",
		# Remove potentially invalid scripts after checking?
		"default_clean_invalid" : "False",
		# Percentage of elements in a condition that may be mutated. Setting this to 0 will still allow 1 mutation per condition.
		"cond_mut_limit" : "1.0"
		}
		return DEFAULT_CONFIG