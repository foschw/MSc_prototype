#!/usr/bin/env python3
import os
def get_default_config(conf_path="mauris.conf"):
	# This dict contains the standard config of MAURIS, i.e. every tunable variable
	# All mappings are string -> string
	DEFAULT_CONFIG = {
	# The minimal timeout for each script execution in s
	"min_timeout" : "1",
	# Timeout for the unit test execution in s
	"unittest_timeout" : "10",
	# Overhead for the generation time limit
	"best_overhead" : "0.9",
	# Default Time limit for the generation algorithm in s
	"default_gen_time" : "900",
	# Default binary output file for rejected strings
	"default_rejected" : "rejected.bin",
	# Maximum attempts of how often a valid string gets mutated to get an invalid string
	"max_mut_attempts" : "10000",
	# The type of arguments used by the tracer. Using str is recommended.
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
	# Indicates whether the mutation algorithm should: only use the most complex string ("0") or all ("1")
	"variable_base" : "1",
	# Set to 1 to allow blind modifications whenever there are no guided ones. This increases the required time and space (drive and memory) significantly, but the results may improve.
	"blind_continue" : "0",
	# Amount of threads that the test tools (check_results and run_unittests) should use
	"test_threads" : "16"
	,
	# Set to 1 to stop mutation early (i.e. directly after the mutated string is accepted)
	"early_stop" : "1"
	,
	}
	if conf_path and os.path.exists(conf_path):
		with open(conf_path, "r", encoding="UTF-8") as conf:
			try:
				conf_override = eval(conf.read())
			except:
				return DEFAULT_CONFIG
		if type(conf_override) == type({}):
			for key in conf_override.keys():
				DEFAULT_CONFIG[key] = conf_override[key]

	return DEFAULT_CONFIG