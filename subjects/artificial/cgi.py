#!/usr/bin/env python3
# This is the CGI decode function as shown in the course (source: https://github.com/vrthra/pychains)
# New in this version: A small testsuite
import sys
import unittest

hex_values = {
    '0': 0,
    '1': 1,
    '2': 2,
    '3': 3,
    '4': 4,
    '5': 5,
    '6': 6,
    '7': 7,
    '8': 8,
    '9': 9,
    'a': 10,
    'b': 11,
    'c': 12,
    'd': 13,
    'e': 14,
    'f': 15,
    'A': 10,
    'B': 11,
    'C': 12,
    'D': 13,
    'E': 14,
    'F': 15,
}

class TestDecode(unittest.TestCase):
    def test_percent_valid_1(self):
        self.assertEqual(cgi_decode("a%20"),"a ")

    def test_percent_valid_2(self):
        self.assertEqual(cgi_decode("z%4b"),"zK")

    def test_percent_invalid_1(self):
        with self.assertRaises(Exception):
            cgi_decode("a%")

    def test_percent_invalid_2(self):
        with self.assertRaises(Exception):
            cgi_decode("a%g1")

    def test_percent_invalid_3(self):
        with self.assertRaises(Exception):
            cgi_decode("a%1")

    def test_normal_1(self):
        self.assertEqual(cgi_decode("test"), "test")

    def test_normal_2(self):
        self.assertEqual(cgi_decode("http://www.google.com"), "http://www.google.com")

    def test_plus(self):
    	self.assertEqual(cgi_decode("1+2"), "1 2")

    def test_empty_string(self):
    	self.assertEqual(cgi_decode(""), "")

def cgi_decode(s):
    t = ""
    i = 0
    state = 0
    val = iter(s)
    while True:
        if state == 1:
            c = next(val, '')
            if c == '' or c not in hex_values:
                raise Exception('0')
            digit_high = c
            i = i + 1
            state = 2
        elif state == 2:
            c = next(val, '')
            if c == '' or c not in hex_values:
                raise Exception('0')
            digit_low = c
            i = i + 1
            state = 3
        elif state == 3:
            v = hex_values[digit_high] * 16 + hex_values[digit_low]
            t = t + chr(v)
            state = 0
        elif state == 0:
            c = next(val, '')
            if c == '':
                return t
            if c == '+':
                t = t + ' '
            elif c == '%':
                state = 1
                i = i + 1
            else:
                t = t + c
            i = i + 1
    return t

def main(arg):
    r = cgi_decode(arg)
    print('Result: %s ' % repr(r))

# REMARK: We need at least one statement after a function call
# this statement is used as the point of return for the call
# in the CFG
if __name__ == '__main__':
    main(sys.argv[1])
