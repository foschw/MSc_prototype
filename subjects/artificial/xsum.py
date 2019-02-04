#!/usr/bin/env python3
import sys
import unittest

class TestXSum(unittest.TestCase):
	def test_valid_1(self):
		self.assertEqual(main("123"),6)

	def test_valid_2(self):
		self.assertEqual(main("99"),18)

	def test_invalid_1(self):
		with self.assertRaises(Exception):
			main("-1")

	def test_invalid_2(self):
		with self.assertRaises(Exception):
			main("34a")


def main(val):
    sum = 0
    for e in val:
        if e in "0123456789":
            sum += int(e)
        else: raise Exception("NaN")
    return sum

if __name__ == "__main__":
    xsum = main(sys.argv[1])
    print(xsum)
