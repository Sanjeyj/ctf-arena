import ast
import os
import logging

logger = logging.getLogger(__name__)

RESTRICTED_MODULES = {"os", "subprocess", "socket", "requests", "urllib"}
RESTRICTED_FUNCTIONS = {"eval", "exec", "compile"}

class PluginASTVisitor(ast.NodeVisitor):
    def __init__(self):
        self.status = "SAFE"
        self.reasons = []

    def visit_Import(self, node):
        for alias in node.names:
            base_module = alias.name.split('.')[0]
            if base_module in RESTRICTED_MODULES:
                self.status = "BLOCKED"
                self.reasons.append(f"Restricted module import: '{alias.name}'")
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            base_module = node.module.split('.')[0]
            if base_module in RESTRICTED_MODULES:
                self.status = "BLOCKED"
                self.reasons.append(f"Restricted module import from: '{node.module}'")
        self.generic_visit(node)

    def visit_Call(self, node):
        # Check for blocked functions like eval, exec, compile
        if isinstance(node.func, ast.Name):
            if node.func.id in RESTRICTED_FUNCTIONS:
                self.status = "BLOCKED"
                self.reasons.append(f"Restricted function call: '{node.func.id}()'")
        
        # Check for open(..., 'w'/'a'/'x'/'+')
        elif isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            # E.g., os.system
            if node.func.value.id in RESTRICTED_MODULES or node.func.attr in RESTRICTED_FUNCTIONS:
                self.status = "BLOCKED"
                self.reasons.append(f"Restricted attribute call: '{node.func.value.id}.{node.func.attr}()'")
        
        self.generic_visit(node)

class PluginSecurity:
    @staticmethod
    def scan_plugin(plugin_dir):
        """Scan all Python files in a plugin directory using AST static analysis.
        
        Returns:
            ("SAFE" | "WARNING" | "BLOCKED", [reasons])
        """
        visitor = PluginASTVisitor()
        
        if not os.path.exists(plugin_dir):
            return "BLOCKED", ["Plugin directory does not exist"]

        python_files = []
        for root, _, files in os.walk(plugin_dir):
            for file in files:
                if file.endswith(".py"):
                    python_files.append(os.path.join(root, file))

        for py_file in python_files:
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Check for raw string mentions as a warning indicator (e.g. system commands in strings)
                lower_content = content.lower()
                for dangerous_str in ["subprocess", "system(", "socket("]:
                    if dangerous_str in lower_content:
                        if visitor.status != "BLOCKED":
                            visitor.status = "WARNING"
                            visitor.reasons.append(f"Suspicious string '{dangerous_str}' found in {os.path.basename(py_file)}")

                tree = ast.parse(content, filename=py_file)
                visitor.visit(tree)
                
            except Exception as e:
                logger.error(f"[PluginSecurity] Failed parsing {py_file}: {str(e)}")
                return "BLOCKED", [f"Syntax/Parse error in {os.path.basename(py_file)}: {str(e)}"]

        # Deduplicate reasons
        unique_reasons = list(set(visitor.reasons))
        return visitor.status, unique_reasons
