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
		self.package_dir = package_dir
		self.compute_targets(script)

	def compute_targets(self, script):
		if not script.endswith(".py"):
			script = script + ".py"
		script = os.path.abspath(script).replace("\\","/")
		if not self.package_dir:
			self.package_dir = TidyDir(script)
		for subdir in self.package_dir.get_subdirs():
			if os.path.exists(str(subdir) + "__init__.py") or str(subdir) == str(self.package_dir):
				files_for_dir = []
				for filename in glob.iglob(str(subdir) + "*"):
					filename = filename.replace("\\", "/")
					if (filename.endswith(".py") and not filename.endswith("__init__.py")) or (os.path.isdir(filename) and os.path.exists(filename + "/__init__.py")):
						if os.path.isdir(filename):
							filename = filename + "/"
						filename = filename[len(subdir):]
						files_for_dir.append(filename)
				self.dirs_avail[str(subdir)] = files_for_dir

	# Only usable for .py files
	def is_import_target(self, other, current, level=0):
		imp_target = self.get_import_path(other, current, level) + ".py"
		return imp_target[imp_target.rfind("/")+1:] in self.dirs_avail[str(TidyDir(imp_target))]

	def is_composite(self, short_path, parent, level=0):
		full_path = str(TidyDir(self.get_import_path(short_path, parent, level) + "/", guess=False))
		return full_path in self.dirs_avail.keys()

	def get_import_path(self, imp_name, curr_dir, level=0):
		# Not an ImportFrom, sanitize dots
		imp_target = imp_name.replace(".","/")
		# Import is relative to package_dir
		if level == 0:
			return str(self.package_dir) + imp_target
		# Import is relative to curr_dir
		elif level == 1:
			return str(TidyDir(curr_dir)) + imp_target
		# Import is relative to ..curr_dir
		elif level == 2:
			return str(TidyDir(os.path.abspath(curr_dir + "/../"))) + imp_name
		# Relative imports with 3 or more levels are rare and likely to cause issues, not handled.
		else:
			raise NotImplementedError("Relative import with three or more dots are not supported.")

	def abs_path_to_impname(self, abs_path):
		abs_path = str(TidyDir(abs_path+"/"))
		other = str(self.package_dir)
		pf = ""
		for i in range(min(len(abs_path),len(other))):
			if abs_path[i] == other[i]:
				pf = pf + other[i]
			else:
				break
		if not pf.endswith("/"):
			pf = pf[:pf.rfind("/")]
		return abs_path[len(pf):-1].replace("/",".")


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

def rewrite_imports(script, mod_cnt=0, glob_name_rename={}):
	with open(script, "r", encoding="UTF-8") as sf:
		scr_ast = ast.fix_missing_locations(ast.parse(sf.read()))

	# Transforms imports to be organized properly. Relative imports are turned absolute, ImportFrom is split in package and py-files, packages are split into multiple single py imports.
	preproc = PreprocessImports(script)
	scr_ast = get_proper_ast(preproc.visit(scr_ast))

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
	asname_name = preproc.asname_name

	# Get renamed versions of all import targets
	for node in getDFSOrder(scr_ast):
		if isinstance(node, ast.Import) and packImpHandler.is_import_target(node.names[0].name, script):
			if node.names[0].asname is not None:
				trgt_name = node.names[0].asname
				asname_name[trgt_name] = node.names[0].name
			else:
				trgt_name = node.names[0].name
				if asname_name.get(trgt_name) is None:
					asname_name[trgt_name] = trgt_name

			# Works for normal imports only
			import_mods[trgt_name] = (rewrite_imports(packImpHandler.get_import_path(node.names[0].name, script) + ".py", mod_cnt+1, glob_name_rename))
		elif isinstance(node, ast.ImportFrom):
			mod_nm = node.module if node.module else ""
			full_path = node.module + "." + node.names[0].name if node.module else node.names[0].name
			# * imports are not possible here due to preprocessing
			try:
				ec = packImpHandler.is_import_target(full_path, script, node.level)
			except:
				ec = None
			ecc = packImpHandler.is_import_target(mod_nm, script, node.level)
			if ec is not None or ecc:
				if ec:
					print("Eat script with dot:", repr(astunparse.unparse(node)))
				elif node.names[0].name == "*":
					print("All of it:", repr(astunparse.unparse(node)))
				else:
					print("Var_names:", repr(astunparse.unparse(node)))

	# Rename using glob_name_rename mapping
	new_ast = ImportInlineTransformer(import_mods).visit(rename_from_dict(script, asname_name, scr_ast, glob_name_rename))

	return get_proper_ast(new_ast)

def get_path_for_name(abs_script_path, asname_name, ast_target_name):
	# Map back all unknown imports to themselves
	if not ast_target_name in asname_name:
		return ast_target_name
	# Let the import handler do the mapping
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
			srcctx = astunparse.unparse(tree_node.value)
			srcctx = srcctx if not srcctx.endswith("\n") else srcctx[:-1]
			tpath = get_path_for_name(abs_script_path, asname_name, srcctx) + ".py"
			if tpath in glob_name_rename.keys():
				nn = ast.Name()
				nn.id = glob_name_rename[tpath][tree_node.attr]
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

class PreprocessImports(ast.NodeTransformer):
	def __init__(self, invoking_script, asname_name={}):
		super().__init__()
		self.invoking_script = invoking_script
		self.asname_name = asname_name

	def flatten_imports(self, module_name, import_alias, source_script, level, name_ref=None, init_pre=None):
		flattened = []
		full_path = module_name + "." + import_alias.name if module_name else import_alias.name
		ilvl = level if level is not None else 0
		if not packImpHandler.is_composite(full_path, source_script, ilvl):
			# ast.ImportFrom
			if level is not None:
				flat_nd = ast.ImportFrom()
				flat_nd.module = module_name
				flat_nd.level = level

			# ast.Import
			else:
				flat_nd = ast.Import()

			if name_ref is not None:
				# Fix asname_name mapping
				name_prefix = packImpHandler.abs_path_to_impname(str(TidyDir(packImpHandler.get_import_path(full_path, source_script,ilvl)+"/", guess=False)))
				self.asname_name[name_ref + "." + import_alias.name[len(init_pre)+1:]] = import_alias.name
	
			flat_nd.names = [import_alias]
			flattened.append(flat_nd)

		else:
			# Turn everything into ast.Import elements and fix the internal mapping
			my_path = str(TidyDir(packImpHandler.get_import_path(full_path, source_script,ilvl)+"/", guess=False))
			name_prefix = packImpHandler.abs_path_to_impname(my_path)
			# Save the initial referencing name and what part of the name needs to be cut off for the mapping
			if name_ref is None:
				name_ref = import_alias.asname if import_alias.asname else import_alias.name
			if init_pre is None:
				init_pre = name_prefix
			for imp_target in packImpHandler.dirs_avail[my_path]:
				imp_target = imp_target[:-1] if imp_target.endswith("/") else imp_target[:-3]
				new_alias = ast.alias()
				new_alias.name = name_prefix + "." + imp_target
				new_alias.asname = None
				flattened = flattened + self.flatten_imports("", new_alias, source_script, None, name_ref, init_pre)

		return flattened

	def visit_Import(self, tree_node):
		mod = ast.Module()
		mod.body = []
		for trgt in tree_node.names:
			mod.body = mod.body + self.flatten_imports("", trgt, self.invoking_script, None)
		return mod

	def visit_ImportFrom(self, tree_node):
		# Check whether the origin is a py-file or composite
		tnm = "" if not tree_node.module else tree_node.module
		if packImpHandler.is_composite(tnm, self.invoking_script, tree_node.level):
			if tree_node.names[0].name != "*":
				# Turn the list into atomic ImportFrom elements
				new_mod = ast.Module()
				new_mod.body = []
				for imp_nd_tgt in tree_node.names:
					new_mod.body = new_mod.body + self.flatten_imports(tnm, imp_nd_tgt, self.invoking_script, tree_node.level)
				return new_mod
			# Handle * here to not clutter flatten_imports
			else:
				new_mod = ast.Module()
				new_mod.body = []
				for target_py in packImpHandler.dirs_avail[str(TidyDir(packImpHandler.get_import_path(tnm, self.invoking_script,tree_node.level)+"/", guess=False))]:
					# Go back to python naming
					target_py = target_py[:-3] if target_py.endswith(".py") else target_py[:-1]
					# Don't import yourself
					rel_target = tree_node.module + "." + target_py if tree_node.module else target_py
					if packImpHandler.get_import_path(rel_target, self.invoking_script,tree_node.level) + ".py" == self.invoking_script:
						continue
					target_alias = ast.alias()
					target_alias.name = target_py
					target_alias.asname = None
					new_mod.body = new_mod.body + self.flatten_imports(tnm, target_alias, str(TidyDir(packImpHandler.get_import_path(tnm, self.invoking_script,tree_node.level)+"/", guess=False)), tree_node.level)

				return new_mod

		else:
			# Don't change anything (no separation!), mapping the names later if necessary is enough
			return tree_node

def main(script, package_dir=None):
	script = os.path.abspath(script).replace("\\","/")

	global packImpHandler
	packImpHandler = ImportHandler(script, package_dir)

	return astunparse.unparse(rewrite_imports(script))

if __name__ == "__main__":
	if len(sys.argv) < 2:
		raise SystemExit("Please specify a py file!")
	if len(sys.argv) < 3:
		print(main(sys.argv[1]))
	else:
		print(main(sys.argv[1], sys.argv[2]))