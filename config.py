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
		# The type of arguments to trace. taintedstr.tstr is recommended for accuracy, using str may help speed
		"trace_type" : "taintedstr.tstr('')",
		# Default folder where mutation results are stored
		"default_mut_dir" : "mutants/",
		# The timeout from the actual script execution is calcualted as int(multi*(slowest seen execution)) + 1. Multi can be adjusted here (default is 2).
		"timeout_slow_multi" : "2",
		# Remove potentially invalid scripts after checking?
		"default_clean_invalid" : "False",
		# File containing the adjustments of relative imports
		"default_imp_tmp" : "loc_level.dict"
		}
		return DEFAULT_CONFIG