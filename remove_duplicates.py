import sys
import functools
import glob
import os
import concurrent.futures
from config import get_default_config
from threading import Lock

os_lock = Lock()

# Returns a list of pairs of start and end indexes which distributes the total amount of work approximately evenly on all threads
def compute_distribution(num_threads, lng):
    res = []
    combs = (lng*(lng-1))/2
    lmt = combs/num_threads
    idxs = 0
    idxe = 1
    acc = 0
    if lng <= num_threads:
        for i in range(lng):
            res.append((i, i+1))
    else:
        for i in range(lng):
            acc += (lng-i-1)
            if acc <= lmt:
                idxe += 1
            else:
                if len(res) == num_threads-1:
                    idxe = lng
                    i = lng
                res.append((idxs, idxe))
                acc = 0
                idxs = idxe
                idxe = idxe+1

    if res[-1][1] != lng:
        res.append((res[-1][1],lng))

    return res

# Reads a file and returns both its content and the content's hash using a cache. Used for finding straight duplicate mutant files.
@functools.lru_cache(maxsize=None)
def read_file_hashed(filename):
    with os_lock:
        with open(filename, "r", encoding="UTF-8") as fli:
            res = fli.read()
            return (res,hash(res))

def compare_index(idx0, idxe, files):
    dups = []

    for idx1 in range(idx0, idxe):
        print("Thread " + str(idx0) + ":", str(idx1+1) + "/" + str(idxe) + "\n", flush=True)
        s1 = read_file_hashed(files[idx1])
        for idx2 in range(idx1+1,len(files)):
            fl2 = files[idx2]
            s2 = read_file_hashed(fl2)
            if s1[1] == s2[1] and s1[0] == s2[0]:
                with os_lock:
                    if os.path.exists(fl2):
                        dups.append(fl2)
                        os.remove(fl2)

    return dups

# Simple duplicate removal method - given a file directory (mutation results), a file extension (.py) as well as the list of (mutant, cause) pairs
# Removes all duplicates (i.e. same content) from both the file-system and the list of pairs
def remove_duplicates(fdir, ext, pairlst):
    print("Removing duplicates...", flush=True)
    global current_config
    current_config = get_default_config()
    ext = ext if not ext.startswith(".") else ext[1:]
    fdir = fdir if not fdir.endswith("/") else fdir[:-1]
    files = []
    dups = []
    for fl in glob.glob(fdir + "/*." + ext):
        fl = fl.replace("\\", "/")
        files.append(fl)

    if len(files) < 2:
        return pairlst

    num_threads = int(current_config["test_threads"])
    future_to_index = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as tpe:
        for (idx1, idxe) in compute_distribution(num_threads, len(files)):
            future_to_index[tpe.submit(compare_index, idx1, idxe, files)] = idx1

        for future in concurrent.futures.as_completed(future_to_index):
            dups = dups + future.result()

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