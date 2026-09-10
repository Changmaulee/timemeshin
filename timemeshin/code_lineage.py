"""
TimeMeshin Level 3: AST & Code Mutation Lineage Engine
Extracts semantic function/class AST diffs, line-level deltas, and causal code mutations.
"""

import ast
import difflib
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

class ASTCodeAnalyzer:
    """Analyzes source code files and extracts semantic AST nodes and diff mutations."""

    @staticmethod
    def parse_python_ast(source_code: str) -> Dict[str, Any]:
        """Extracts top-level and nested classes, functions, and imports from Python code."""
        results = {
            "classes": {},
            "functions": {},
            "imports": []
        }
        try:
            tree = ast.parse(source_code)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                    results["classes"][node.name] = {
                        "name": node.name,
                        "line": node.lineno,
                        "methods": methods,
                        "docstring": ast.get_docstring(node) or ""
                    }
                elif isinstance(node, ast.FunctionDef):
                    results["functions"][node.name] = {
                        "name": node.name,
                        "line": node.lineno,
                        "args": [a.arg for a in node.args.args],
                        "docstring": ast.get_docstring(node) or ""
                    }
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        results["imports"].append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    results["imports"].append(f"{node.module}")
        except Exception:
            pass # Fallback on syntax errors in half-typed files
        return results

    @staticmethod
    def compute_code_diff(old_code: str, new_code: str, filepath: str = "file.py") -> Dict[str, Any]:
        """Computes Myers unified diff and semantic AST structural mutations."""
        old_lines = old_code.splitlines(keepends=True)
        new_lines = new_code.splitlines(keepends=True)
        
        diff = difflib.unified_diff(old_lines, new_lines, fromfile=f"a/{filepath}", tofile=f"b/{filepath}", lineterm="")
        patch = "".join(diff)
        
        # Semantic AST analysis if Python
        mutations = []
        is_python = filepath.endswith(".py")
        
        if is_python:
            old_ast = ASTCodeAnalyzer.parse_python_ast(old_code)
            new_ast = ASTCodeAnalyzer.parse_python_ast(new_code)
            
            # Detect added/modified functions
            for fn_name, fn_meta in new_ast["functions"].items():
                if fn_name not in old_ast["functions"]:
                    mutations.append({
                        "type": "FUNCTION_ADDED",
                        "entity": f"function:{fn_name}",
                        "details": f"Added function '{fn_name}({', '.join(fn_meta['args'])})' at line {fn_meta['line']}"
                    })
                elif old_ast["functions"][fn_name] != fn_meta:
                    mutations.append({
                        "type": "FUNCTION_MODIFIED",
                        "entity": f"function:{fn_name}",
                        "details": f"Modified function '{fn_name}' structure"
                    })
                    
            # Detect deleted functions
            for fn_name in old_ast["functions"]:
                if fn_name not in new_ast["functions"]:
                    mutations.append({
                        "type": "FUNCTION_DELETED",
                        "entity": f"function:{fn_name}",
                        "details": f"Deleted function '{fn_name}'"
                    })
                    
            # Detect class mutations
            for cls_name, cls_meta in new_ast["classes"].items():
                if cls_name not in old_ast["classes"]:
                    mutations.append({
                        "type": "CLASS_ADDED",
                        "entity": f"class:{cls_name}",
                        "details": f"Added class '{cls_name}' with methods {cls_meta['methods']}"
                    })

        # Line metrics
        added_lines = sum(1 for line in patch.splitlines() if line.startswith("+") and not line.startswith("+++"))
        removed_lines = sum(1 for line in patch.splitlines() if line.startswith("-") and not line.startswith("---"))

        return {
            "filepath": filepath,
            "patch": patch,
            "added_lines": added_lines,
            "removed_lines": removed_lines,
            "semantic_mutations": mutations,
            "old_hash": hashlib.sha256(old_code.encode("utf-8")).hexdigest()[:12],
            "new_hash": hashlib.sha256(new_code.encode("utf-8")).hexdigest()[:12],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
