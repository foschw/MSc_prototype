#!/usr/bin/env python3
import sys
import unittest

class TestXSum(unittest.TestCase):
	def test_valid_1(self):
		self.assertEqual(main("123"),6)

	def test_valid_2(self):
		self.assertEqual(main("99"),18)

	def test_invalid_1(self):
		with self.assertRaises(CustomException):
			main("-1")

	def test_invalid_2(self):
		with self.assertRaises(CustomException):
			main("34a")

class CustomException(Exception):
    def __init__(self, message):
        super(CustomException, self).__init__(message)
        try:
            num = int(message)
        except:
            num = 1

        if num is not None and num > 1:
            self.message = "Found " + str(num) + " bad elements."
        else:
            self.message = "Found " + str(num) + " bad element."

def main(val):
    sum = 0
    for e in val:
        if e not in "0123456789":
            raise CustomException("NaN")
        else: sum += int(e)
    return sum

if __name__ == "__main__":
    xsum = main(sys.argv[1])
    print(xsum)
