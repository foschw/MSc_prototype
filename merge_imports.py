import sys
import ast
import os
import astunparse
import glob
from tidydir import TidyDir

# Methods for handling imports across a project directory
packImpHandler = None

class ImportHandler():
	def __init__(self, script, package_dir=None):
		self.dirs_avail = {}
		self.script = script
		self.package_dir = package_dir
		self.compute_py_targets()

	def compute_py_targets(self):
		if not self.script.endswith(".py"):
			self.script = script + ".py"
		self.script = os.path.abspath(self.script).replace("\\","/")
		if not self.package_dir:
			self.package_dir = TidyDir(self.script)
		for subdir in self.package_dir.get_subdirs():
			if os.path.exists(str(subdir) + "__init__.py") or str(subdir) == str(self.package_dir):
				files_for_dir = []
				for filename in glob.iglob(str(subdir) + "*.py"):
					filename = filename.replace("\\", "/")
					if not filename.endswith("__init__.py"):
						filename = filename[len(subdir):-3]
						files_for_dir.append(filename)
				self.dirs_avail[str(subdir)] = files_for_dir

	def is_import_target(self, other, current, level=None):
		imp_target = self.get_import_path(other, current, level)
		return imp_target[imp_target.rfind("/")+1:-3] in self.dirs_avail[str(TidyDir(imp_target))]

	def get_import_path(self, imp_name, curr_dir, level=None):
		# Not an ImportFrom, sanitize dots
		if not level:
			level = 0 if imp_name.find(".") != -1 else 1
			imp_target = imp_name.replace(".","/")
			# Add back a dot to make handler below applicable
			imp_target = "." + imp_target if level > 0 else imp_target
				
		# Import is relative to package_dir
		if level == 0:
			imp_target = imp_name.replace(".","/")
			return str(self.package_dir) + imp_target + ".py"
		# Import is relative to curr_dir
		elif level == 1:
			return str(TidyDir(curr_dir)) + imp_name[1:] + ".py"
		# Import is relative to ..curr_dir
		elif level == 2:
			return str(TidyDir(os.path.abspath(curr_dir + "/../"))) + imp_name[2:] + ".py"
		# Relative imports with 3 or more levels are rare and likely to cause issues, not handled yet.
		else:
			raise NotImplementedError("Relative import with three or more dots are not supported.")

class DFSVisitor(ast.NodeVisitor):
	def __init__(self):
		super().__init__()
		self.entries = []

	def generic_visit(self, tree_node):
		self.entries.append(tree_node)
		super().generic_visit(tree_node)

def getDFSOrder(some_ast):
	mvisit = DFSVisitor()
	mvisit.visit(some_ast)
	return mvisit.entries

def get_proper_ast(some_ast):
	return ast.fix_missing_locations(ast.parse(astunparse.unparse(some_ast)))

def get_global_vars(mod_ast):
	# 0: Global scope only
	scope = 0
	locend = []
	globnames = set()
	for tree_node in getDFSOrder(mod_ast):

		if len(locend) > 0 and hasattr(tree_node, "lineno") and tree_node.lineno > locend[-1]:
			scope -= 1
			locend = locend[:-1]

		if isinstance(tree_node, ast.FunctionDef):
			if scope == 0:
				globnames.add(tree_node.name)
			# >= 1: Function scope available
			scope += 1
			# Final line of the local scope
			locend.append(tree_node.body[-1].lineno)

		elif isinstance(tree_node, ast.Global):
			for gname in tree_node.names:
				globnames.add(gname)

		elif isinstance(tree_node, ast.Assign):
			if scope == 0:
				for trgt in tree_node.targets:
					globnames.add(trgt.id)

		elif isinstance(tree_node, ast.AugAssign):
			if scope == 0:
				globnames.add(tree_node.target.id)

		elif isinstance(tree_node, ast.ClassDef):
			if scope == 0:
				globnames.add(tree_node.name)

	return globnames

def avoid_rename_collision(sc_path, sc_var_name, glob_name_rename, cnt):
	prefix = "s" + str(cnt) + "_"
	name_clean = False
	while not name_clean:
		name_clean = True
		for ren_dict_name in glob_name_rename.keys():
			if ren_dict_name == sc_path:
				continue
			else:
				for var_name in list(glob_name_rename[ren_dict_name].values()) + list(glob_name_rename[ren_dict_name].values()):
					if prefix + sc_var_name == var_name:
						name_clean = False
						prefix = prefix[0] + "0" + prefix[1:]
						break

	return prefix + sc_var_name


def rename(sc_path, glob_name_rename, cnt):
	for ren_dict_name in glob_name_rename.keys():
		if ren_dict_name == sc_path:
			continue
		else:
			for var_name in glob_name_rename[ren_dict_name].values():
				if not var_name.startswith("_") and glob_name_rename[sc_path].get(var_name) == -1:
					glob_name_rename[sc_path][var_name] = avoid_rename_collision(sc_path, var_name, glob_name_rename, cnt)

	return glob_name_rename

def rewrite_imports(script, package_dir=None, mod_cnt=0, glob_name_rename={}):
	with open(script, "r", encoding="UTF-8") as sf:
		scr_ast = ast.fix_missing_locations(ast.parse(sf.read()))

	# Only one import per line
	scr_ast = get_proper_ast(UnfoldImports().visit(scr_ast))
	global packImpHandler
	# Collect all import targets in the project directory
	if not packImpHandler:
		packImpHandler = ImportHandler(script, package_dir)

	# Initialize renaming rules
	name_rename = {}

	for gname in get_global_vars(scr_ast):
		# Use -1 instead of None to be able to use get()
		name_rename[gname] = -1

	glob_name_rename[script] = name_rename

	glob_name_rename = rename(script, glob_name_rename, mod_cnt)

	for g_var in glob_name_rename[script].keys():
		if glob_name_rename[script][g_var] == -1:
			glob_name_rename[script][g_var] = g_var

	import_mods = {}
	asname_name = {}

	# Get renamed versions of all import targets
	for node in getDFSOrder(scr_ast):
		if isinstance(node, ast.Import) and packImpHandler.is_import_target(node.names[0].name, script):
			if node.names[0].asname is not None:
				trgt_name = node.names[0].asname
				asname_name[trgt_name] = node.names[0].name
			else:
				trgt_name = node.names[0].name
				asname_name[trgt_name] = trgt_name
			# Works for normal imports only
			import_mods[trgt_name] = (rewrite_imports(packImpHandler.get_import_path(node.names[0].name, script), package_dir, mod_cnt+1, glob_name_rename))
	# Rename using glob_name_rename mapping
	new_ast = ImportInlineTransformer(import_mods).visit(rename_from_dict(script, asname_name, scr_ast, glob_name_rename))

	return get_proper_ast(new_ast)

def get_path_for_name(abs_script_path, asname_name, ast_target_name):
	# Map back all unknown imports to themselves
	if not ast_target_name in asname_name:
		return ast_target_name
	# Let the import handler do the mapping
	global packImpHandler
	# Non-relative import
	return packImpHandler.get_import_path(asname_name[ast_target_name], abs_script_path)

def in_loc_scope(name, scope, scope_dict):
	if scope < 1:
		return False

	for i in range(1, scope+1):
		if name in scope_dict[i]:
			return True

	return False

def rename_from_dict(abs_script_path, asname_name, scr_ast, glob_name_rename):
	scope = 0
	locend = []
	globonly = {}
	locvars = {}
	dfsord = getDFSOrder(scr_ast)
	for idx in range(len(dfsord)):
		tree_node = dfsord[idx]

		if len(locend) > 0 and hasattr(tree_node, "lineno") and tree_node.lineno > locend[-1]:
			globonly.pop(scope)
			locvars.pop(scope)
			scope -= 1
			locend = locend[:-1]

		if isinstance(tree_node, ast.FunctionDef):
			# >= 1: Function scope available
			is_class_fn = False
			for aarg in tree_node.args.args:
				if aarg.arg == "self":
					is_class_fn = True
					break

			if scope == 0 and not is_class_fn:
				tree_node.name = glob_name_rename[abs_script_path][tree_node.name]
			elif scope > 1:
				locvars[scope-1].add(tree_node.name)
			scope += 1
			globonly[scope] = set()
			locvars[scope] = set()
			if tree_node.args.kwarg:
				locvars[scope].add(tree_node.args.kwarg.arg)
			for kwo in tree_node.args.kwonlyargs:
				locvars[scope].add(kwo.arg)
			if tree_node.args.vararg:
				locvars[scope].add(tree_node.args.vararg.arg)
			for aarg in tree_node.args.args:
				locvars[scope].add(aarg.arg)
			# Final line of the local scope
			locend.append(tree_node.body[-1].lineno)

		elif isinstance(tree_node, ast.Global):
			for gname in tree_node.names:
				globonly[scope].add(gname)

		elif isinstance(tree_node, ast.Assign):
			for trgt in tree_node.targets:
				if isinstance(trgt, ast.Name):
					if scope == 0 or trgt.id in globonly[scope]:
						trgt.id = glob_name_rename[abs_script_path][trgt.id]
					else:
						locvars[scope].add(trgt.id)

		elif isinstance(tree_node, ast.AugAssign):
			if isinstance(tree_node.target, ast.Name):
				if scope == 0 or tree_node.target.id in globonly[scope]:
					tree_node.target.id = glob_name_rename[abs_script_path][tree_node.target.id]
				else:
					locvars[scope].add(tree_node.target.id)

		elif isinstance(tree_node, ast.ClassDef):
			if scope == 0 and glob_name_rename[abs_script_path].get(tree_node.name):
				tree_node.name = glob_name_rename[abs_script_path][tree_node.name]

		elif isinstance(tree_node, ast.Name):
			if scope == 0 or not in_loc_scope(tree_node.id, scope, locvars):
				if glob_name_rename[abs_script_path].get(tree_node.id):
					tree_node.id = glob_name_rename[abs_script_path].get(tree_node.id)

		elif isinstance(tree_node, ast.Attribute):
			if isinstance(tree_node.value, ast.Name) and get_path_for_name(abs_script_path, asname_name, tree_node.value.id) in glob_name_rename.keys():
				nn = ast.Name()
				nn.id = glob_name_rename[get_path_for_name(abs_script_path, asname_name, tree_node.value.id)][tree_node.attr]
				tree_node.value = nn
				tree_node.attr = None

	return FixAttributes().visit(scr_ast)

class ImportInlineTransformer(ast.NodeTransformer):
	def __init__(self, import_dict):
		super().__init__()
		self.import_dict = import_dict

	def visit_Import(self, tree_node):
		tname = tree_node.names[0].asname
		tname = tname if tname else tree_node.names[0].name
		impmod = self.import_dict.get(tname)
		if impmod:
			return impmod
		else:
			return tree_node

class FixAttributes(ast.NodeTransformer):
	def visit_Attribute(self, tree_node):
		if tree_node.attr is None:
			new_node = tree_node.value
			return new_node

		return self.generic_visit(tree_node)

class UnfoldImports(ast.NodeTransformer):
	def visit_Import(self, tree_node):
		mod = ast.Module()
		mod.body = []
		for trgt in tree_node.names:
			imp_nd = ast.Import()
			imp_nd.names = [trgt]
			mod.body.append(imp_nd)
		return mod

def main(script, package_dir=None):
	script = os.path.abspath(script).replace("\\","/")

	return astunparse.unparse(rewrite_imports(script))

if __name__ == "__main__":
	if len(sys.argv) < 2:
		raise SystemExit("Please specify a py file!")
	if len(sys.argv) < 3:
		print(main(sys.argv[1]))
	else:
		print(main(sys.argv[1], sys.argv[2]))