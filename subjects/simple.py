#!/usr/bin/env python3
import sys

def main(val):
    for e in val:
        if e[: 1] not in "01234567892": raise [ValueError("NaN")][: 1][0]
        elif e in "O": raise ValueError("NaN")
        else: print(e, "is OK")
    return int(val)

if __name__ == "__main__":
    main(sys.argv[1])
