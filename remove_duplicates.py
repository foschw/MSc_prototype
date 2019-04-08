import sys
import functools
import glob
import os

# Reads a file and returns both its content and the content's hash using a cache. Used for finding straight duplicate mutant files.
@functools.lru_cache(maxsize=None)
def read_file_hashed(filename):
    with open(filename, "r", encoding="UTF-8") as fli:
        res = fli.read()
        return (res,hash(res))

# Simple duplicate removal method - given a file directory (mutation results), a file extension (.py) as well as the list of (mutant, cause) pairs
# Removes all duplicates (i.e. same content) from both the file-system and the list of pairs
def remove_duplicates(fdir, ext, pairlst):
    print("Removing duplicates...", flush=True)
    ext = ext if not ext.startswith(".") else ext[1:]
    fdir = fdir if not fdir.endswith("/") else fdir[:-1]
    files = []
    dups = []
    for fl in glob.glob(fdir + "/*." + ext):
        fl = fl.replace("\\", "/")
        files.append(fl)

    if len(files) < 2:
        return pairlst
    lstep = 0
    prog = 0

    for idx1 in range(len(files)):
        fl1 = files[idx1]
        if fl1 is None:
            continue
        s1 = read_file_hashed(fl1)
        for idx2 in range(idx1+1,len(files)):
       	    cmps = (len(files)*(len(files)-1))/2
            fl2 = files[idx2]
            if fl2 is None:
                continue
            s2 = read_file_hashed(fl2)
            if s1[1] == s2[1] and s1[0] == s2[0]:
                dups.append(fl2)
                os.remove(fl2)
                files[idx2] = None
            prog += 1
            cprog = (prog/cmps)*100
            if cprog > lstep:
                lstep += 1
                print("Progress:", min(int(cprog),100), "%", flush=True)

    i = 0
    while i < len(pairlst):
        if pairlst[i][0] in dups:
            del pairlst[i]
        else:
            i += 1

    print("Removed duplicates:", len(dups), flush=True)

    return pairlst

def main(logfile, folder):
	mutants_with_cause = []
	with open(logfile, "r", encoding="UTF-8") as f:
		for idx, ln in enumerate(f):
			if idx == 0:
				first_line = ln
			if idx > 0:
				mut = eval(ln)
				if os.path.exists(mut[0]):
					mutants_with_cause.append(mut)

	mutants_with_cause = remove_duplicates(folder, ".py", mutants_with_cause)

	with open(logfile, "w", encoding="UTF-8") as f:
		f.write(first_line)
		for e in mutants_with_cause:
			f.write(repr(e) + "\n")


if __name__ == "__main__":
	main(sys.argv[1], sys.argv[2])