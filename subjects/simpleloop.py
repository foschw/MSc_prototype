#!/usr/bin/env python3
import sys

def main(val):
    for e in val:
        if e[: 1] not in "01234567892":
            raise ValueError("NaN")
        else:
            try:
                int(e)
            except:
                if True:
                    raise ValueError("NaN")
                else:
                    raise ValueError("NaN")
if __name__ == "__main__":
    main(sys.argv[1])
