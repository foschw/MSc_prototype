#!/usr/bin/env python3
import sys

def get_sum_safe(a,b):
	try:
		return int(a) + int(b)
	except:
		return -1

if __name__ == "__main__":
    main(sys.argv[1])
