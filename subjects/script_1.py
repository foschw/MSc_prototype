#!/usr/bin/env python3
import sys
import unittest
from script_2 import get_sum_safe

class TestScript(unittest.TestCase):

	def test_1(self):
		with self.assertRaises(Exception):
			main("1a")

	def test_2(self):
		self.assertEqual(main("14"),56)

def main(val):
	for d in val:
		if d not in "0123456789":
			raise Exception("Not an int")

	return get_sum_safe(int(val),"42")

if __name__ == "__main__":
    res = main(sys.argv[1])
    print(res)