import re
import glob
import os

# Convenience class which consistently handles trailing slashes
class TidyDir:

    def __init__(self, somepath, guess=True):
        re_slashes = re.compile(r"/+")
        self.re_slashes = re_slashes
        if not isinstance(somepath, str):
            somepath = str(somepath)
        somepath = somepath.replace("\\", "/")
        somepath = re.sub(re_slashes, "/", somepath)
        if somepath.find("/") == -1:
            somepath = somepath + "/"
        if guess:
            if somepath.rfind(".") > somepath.rfind("/"):
                somepath = somepath[:somepath.rfind("/")]
        if not somepath.endswith("/"):
            somepath = somepath + "/"
        self.mypath = somepath

    def __add__(self, other):
        if not isinstance(other, TidyDir):
            other = TidyDir(other, guess=False)
        somepath = self.mypath + "/" + other.mypath
        somepath = re.sub(self.re_slashes, "/", somepath)
        if not somepath.endswith("/"):
            somepath = somepath + "/"
        return somepath

    def __str__(self):
        return self.mypath

    def __repr__(self):
        return repr(self.mypath)

    def __getitem__(self, item):
        return self.mypath.__getitem__(item)

    def __len__(self):
        return len(self.mypath)

    def split_path(self, path):
        base = self.mypath
        if not base:
            return ("", path)
        idx = 0
        for i in range(min(len(path),len(base))):
            if path[idx] != base[idx]:
                break
            else:
                idx += 1
        path = path[idx:]
        if path.find("/") >= 0:
            r1 = path[:path.find("/")+1]
            r2 = path[path.find("/")+1:]
        else:
            r1 = ""
            r2 = path
        return (r1, r2)

    def get_subdirs(self):
        res = []
        res.append(self.mypath)
        for fpath in glob.glob(self.mypath + "**/*", recursive=True):
            fpath = fpath.replace("\\", "/")
            if os.path.isdir(fpath):
                res.append(TidyDir(fpath))
        return res