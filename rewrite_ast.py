import ast
import sys
import astunparse

class InRewrite(ast.NodeTransformer):
    def __init__(self):
        super().__init__()
        self.skipped = []

    def visit_Compare(self, tree_node):
        left = tree_node.left
        if not tree_node.ops or not isinstance(tree_node.ops[0], ast.In):
            return tree_node
        wrapped_left = ast.Call()
        wrapped_left.args = [left]
        fname = ast.Name()
        fname.id = "TaintWrapper"
        wrapped_left.func = fname
        wrapped_left.keywords = []
        if hasattr(left, "ctx"):
            mod_val = ast.Call(func=ast.Attribute(value=wrapped_left, attr='in_', ctx=left.ctx),args=tree_node.comparators,keywords=[])
        else:
            mod_val = ast.Call(func=ast.Attribute(value=wrapped_left, attr='in_'),args=tree_node.comparators,keywords=[])
        self.modded = True
        return mod_val

    def visit_ImportFrom(self, tree_node):
        if tree_node.module == "__future__":
            self.skipped.append(astunparse.unparse(tree_node))
            return None
        return self.generic_visit(tree_node)

def rewrite_in(pyfile):
    with open(pyfile, "r", encoding="UTF-8") as f:
        base_ast = ast.fix_missing_locations(ast.parse(f.read()))
        prefix = ""
        try:
            rewrite = InRewrite()
            new_ast = rewrite.visit(base_ast)
            if hasattr(rewrite, "modded"):
                if rewrite.skipped:
                    for ndval in rewrite.skipped:
                        prefix = prefix + ndval + "\n"
                wrapper_ast = ast.fix_missing_locations(ast.parse(prefix + "import taintedstr\nclass TaintWrapper(str):\n\n    def __init__(self, other):\n        if isinstance(other, TaintWrapper):\n            other = other.other\n        self.tainted = isinstance(other, taintedstr.tstr)\n        self.other = other\n\n    def in_(self, cpt):\n        if self.tainted:\n            return self.other.in_(cpt)\n        else:\n            return self.other in cpt\n"))
                new_ast.body = wrapper_ast.body + new_ast.body
            return astunparse.unparse(new_ast)
        except Exception as e:
            print(e)

def main(pyfile):
    # Attaches a wrapper that allows tainting strings.
    print(rewrite_in(pyfile))

# The wrapper code that gets embedded by InRewrite. 
#class TaintWrapper(str):
#   def __init__(self, other):
#       if isinstance(other, TaintWrapper):
#           other = other.other
#       self.tainted = isinstance(other, taintedstr.tstr)
#       self.other = other

#   def in_(self, cpt):
#       if self.tainted:
#           return self.other.in_(cpt)
#       else:
#           return self.other in cpt

if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("Please specify a .py file!")

    main(sys.argv[1])