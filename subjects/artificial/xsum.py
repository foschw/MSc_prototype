#!/usr/bin/env python3
import sys

def main(val):
    sum = 0
    for e in val:
        if e not in "0123456789":
            raise Exception("NaN")
        else: sum += int(e)
    return sum

if __name__ == "__main__":
    xsum = main(sys.argv[1])
    print(xsum)
