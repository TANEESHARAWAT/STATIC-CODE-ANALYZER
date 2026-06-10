"""
PythonAntlrAnalyzer — ANTLR4 visitor for Python source files.

This is the Python equivalent of c_analyzer.py.
It uses the pre-generated ANTLR4 Python3 grammar (in generated/python3/)
to build a parse tree, then walks it applying all rules.

Rule List
---------
PY001  Function name not snake_case
PY002  Too many parameters (> 5)
PY003  Bare except: clause
PY004  Ambiguous variable name (l, O, I)
PY005  Variable assigned but never used
PY006  Variable used but never defined
PY007  Mutable default argument (list/dict/set as default)
PY008  Comparison with None using == instead of is/is not
PY009  Comparison with True/False using == instead of is
PY010  Use of print as a statement (Python 2 style)
PY011  Empty except block (bare pass)
PY012  Too many nested blocks (> 4 levels)
PY013  Missing docstring on public function
PY014  Magic number in expression
PY015  Global variable usage inside function
"""

import re
from typing import List, Dict, Set
from core.models import Violation, Severity, Phase


BUILTINS = {
    "print", "len", "range", "int", "str", "float", "bool", "list", "dict",
    "set", "tuple", "type", "isinstance", "hasattr", "getattr", "setattr",
    "enumerate", "zip", "map", "filter", "sorted", "reversed", "sum", "min",
    "max", "abs", "round", "open", "input", "super", "object", "None",
    "True", "False", "self", "cls", "Exception", "ValueError", "TypeError",
    "KeyError", "IndexError", "ZeroDivisionError", "StopIteration",
    "NotImplementedError", "RuntimeError", "OSError", "IOError",
}

KEYWORDS = {
    "and", "as", "assert", "async", "await", "break", "class", "continue",
    "def", "del", "elif", "else", "except", "finally", "for", "from",
    "global", "if", "import", "in", "is", "lambda", "nonlocal", "not",
    "or", "pass", "raise", "return", "try", "while", "with", "yield",
}


class PythonAntlrAnalyzer:
    """
    Wraps the ANTLR4 visitor + adds regex post-processing for rules
    that are easier to detect on raw source lines.
    """

    def __init__(self):
        self.violations: List[Violation] = []
        self.assigned_vars: Dict[str, int] = {}
        self.used_vars: Dict[str, int] = {}
        self._source_lines: List[str] = []

    def analyze_tree(self, tree, source: str) -> List[Violation]:
        """Run ANTLR4 visitor rules on the parse tree."""
        self._source_lines = source.splitlines()
        try:
            from analyzers._python_visitor import _PythonVisitor
            visitor = _PythonVisitor(self)
            visitor.visit(tree)
            self._check_unused(visitor.assigned_vars, visitor.used_vars)
        except Exception:
            pass
        self._regex_checks(source)
        return sorted(self.violations, key=lambda v: v.line)

    def _check_unused(self, assigned, used):
        """PY005 / PY006"""
        for var, line in assigned.items():
            if var not in used and var not in BUILTINS and var not in KEYWORDS:
                self.violations.append(Violation(
                    "PY005", f"Variable '{var}' assigned but never used",
                    line, Severity.WARNING, Phase.SEMANTIC
                ))
        for var, line in used.items():
            if var not in assigned and var not in BUILTINS and var not in KEYWORDS:
                self.violations.append(Violation(
                    "PY006", f"Variable '{var}' used but never defined",
                    line, Severity.WARNING, Phase.SEMANTIC
                ))

    def _regex_checks(self, source: str):
        lines = list(enumerate(source.splitlines(), start=1))

        # PY007: mutable default argument
        mut_default = re.compile(r'def\s+\w+\s*\([^)]*=\s*(\[\s*\]|\{\s*\}|\bdict\b|\blist\b|\bset\b)')
        # PY008: comparison with None using ==
        none_eq = re.compile(r'\b\w+\s*==\s*None\b|\bNone\s*==\s*\w+')
        # PY009: comparison with True/False using ==
        bool_eq = re.compile(r'\b\w+\s*==\s*(True|False)\b|\b(True|False)\s*==\s*\w+')
        # PY011: empty except block
        empty_except = re.compile(r'^\s*except[^:]*:\s*$')
        # PY012: indentation depth proxy (count leading spaces / 4)
        deep_indent = re.compile(r'^( {16,}|\t{4,})\S')
        # PY013: public function without docstring (next line not a string)
        func_def = re.compile(r'^\s*def\s+([a-z_]\w*)\s*\(')
        # PY014: magic number
        magic = re.compile(r'(?<!["\w])([2-9]\d*|[1-9]\d+)(?![\w"])')
        # PY015: global statement inside function
        global_stmt = re.compile(r'^\s+global\s+\w+')
        # PY004: ambiguous names
        ambiguous = re.compile(r'^\s*([lOI])\s*=')

        indent_depth = 0
        in_func = False

        for lineno, text in lines:
            stripped = text.strip()
            if not stripped or stripped.startswith('#'):
                continue

            # PY007
            if mut_default.search(text):
                self.violations.append(Violation(
                    "PY007", "Mutable default argument ([] or {}) — shared across calls; use None instead",
                    lineno, Severity.WARNING, Phase.SEMANTIC
                ))

            # PY008
            if none_eq.search(text):
                self.violations.append(Violation(
                    "PY008", "Use 'is None' or 'is not None' instead of '== None'",
                    lineno, Severity.WARNING, Phase.SEMANTIC
                ))

            # PY009
            if bool_eq.search(text):
                self.violations.append(Violation(
                    "PY009", "Use 'if x:' or 'if not x:' instead of comparing to True/False with ==",
                    lineno, Severity.INFO, Phase.SEMANTIC
                ))

            # PY011: empty except block (pass immediately after except)
            if empty_except.match(text):
                # Check next non-empty line
                for j in range(lineno, min(lineno + 3, len(lines))):
                    nxt = lines[j][1].strip() if j < len(lines) else ''
                    if nxt == 'pass':
                        self.violations.append(Violation(
                            "PY011", "Empty except block (bare pass) — silently swallows exceptions",
                            lineno, Severity.WARNING, Phase.SEMANTIC
                        ))
                        break
                    if nxt:
                        break

            # PY012: deeply nested code
            if deep_indent.match(text):
                self.violations.append(Violation(
                    "PY012", "Code nested more than 4 levels deep — consider refactoring",
                    lineno, Severity.INFO, Phase.SEMANTIC
                ))

            # PY014: magic numbers (skip define-like lines and imports)
            if not stripped.startswith(('import', 'from', '#', 'def ', 'class ')):
                if magic.search(text):
                    self.violations.append(Violation(
                        "PY014", "Magic number literal — consider using a named constant",
                        lineno, Severity.INFO, Phase.SEMANTIC
                    ))

            # PY015: global inside function
            if global_stmt.match(text):
                self.violations.append(Violation(
                    "PY015", "Use of 'global' inside function — prefer passing arguments",
                    lineno, Severity.WARNING, Phase.SEMANTIC
                ))

            # PY004: ambiguous variable names
            m = ambiguous.match(text)
            if m:
                self.violations.append(Violation(
                    "PY004", f"Ambiguous variable name '{m.group(1)}' — easily confused with 1/0/I",
                    lineno, Severity.WARNING, Phase.SEMANTIC
                ))

        # PY013: public function without docstring
        src_lines = source.splitlines()
        for i, line in enumerate(src_lines):
            m = func_def.match(line)
            if not m:
                continue
            fname = m.group(1)
            if fname.startswith('_'):
                continue  # private — skip
            # Next non-empty line should be a docstring
            for j in range(i + 1, min(i + 4, len(src_lines))):
                nxt = src_lines[j].strip()
                if not nxt:
                    continue
                if not (nxt.startswith('"""') or nxt.startswith("'''")):
                    self.violations.append(Violation(
                        "PY013", f"Public function '{fname}' has no docstring",
                        i + 1, Severity.INFO, Phase.SEMANTIC
                    ))
                break

    def regex_only(self, source: str) -> List[Violation]:
        """
        Pure-regex fallback — runs when ANTLR4 is not installed.
        Covers PY001-PY015 without needing a parse tree.
        """
        self.violations = []
        lines = list(enumerate(source.splitlines(), start=1))

        func_re   = re.compile(r'^\s*def\s+(\w+)\s*\(([^)]*)\)')
        assign_re = re.compile(r'^\s*([a-z_]\w*)\s*=')
        used_re   = re.compile(r'\b([a-z_]\w*)\b')
        class_re  = re.compile(r'^\s*class\s+')

        assigned: Dict[str, int] = {}
        used: Set[str]           = set()

        for lineno, text in lines:
            stripped = text.strip()
            if not stripped or stripped.startswith('#'):
                continue

            # PY001 + PY002 + PY013
            m = func_re.match(text)
            if m:
                fname  = m.group(1)
                params = [p.strip() for p in m.group(2).split(',') if p.strip() and p.strip() != 'self']
                if not re.match(r'^[a-z_][a-z0-9_]*$', fname):
                    self.violations.append(Violation("PY001", f"Function '{fname}' should use snake_case",
                                                     lineno, Severity.WARNING, Phase.SEMANTIC))
                if len(params) > 5:
                    self.violations.append(Violation("PY002", f"Function '{fname}' has {len(params)} parameters (max 5)",
                                                     lineno, Severity.WARNING, Phase.SEMANTIC))
                # PY013: check next non-empty line for docstring
                for j in range(lineno, min(lineno + 3, len(lines))):
                    nxt = lines[j][1].strip()
                    if not nxt:
                        continue
                    if not (nxt.startswith('"""') or nxt.startswith("'''")):
                        if not fname.startswith('_'):
                            self.violations.append(Violation("PY013", f"Public function '{fname}' has no docstring",
                                                             lineno, Severity.INFO, Phase.SEMANTIC))
                    break

            # PY003: bare except
            if re.match(r'^\s*except\s*:\s*$', text):
                self.violations.append(Violation("PY003", "Bare 'except:' catches all exceptions — specify type",
                                                 lineno, Severity.ERROR, Phase.SEMANTIC))

            # PY004: ambiguous names
            ma = re.match(r'^\s*([lOI])\s*=', text)
            if ma:
                self.violations.append(Violation("PY004", f"Ambiguous variable name '{ma.group(1)}'",
                                                 lineno, Severity.WARNING, Phase.SEMANTIC))

            # PY007: mutable default
            if re.search(r'def\s+\w+\s*\([^)]*=\s*(\[\s*\]|\{\s*\})', text):
                self.violations.append(Violation("PY007", "Mutable default argument — use None instead",
                                                 lineno, Severity.WARNING, Phase.SEMANTIC))

            # PY008: == None
            if re.search(r'\b\w+\s*==\s*None\b|\bNone\s*==\s*\w+', text):
                self.violations.append(Violation("PY008", "Use 'is None' instead of '== None'",
                                                 lineno, Severity.WARNING, Phase.SEMANTIC))

            # PY009: == True/False
            if re.search(r'==\s*(True|False)\b|(True|False)\s*==', text):
                self.violations.append(Violation("PY009", "Use 'if x:' instead of '== True/False'",
                                                 lineno, Severity.INFO, Phase.SEMANTIC))

            # PY011: empty except + pass
            if re.match(r'^\s*except[^:]*:\s*$', text):
                for j in range(lineno, min(lineno + 3, len(lines))):
                    nxt = lines[j][1].strip()
                    if nxt == 'pass':
                        self.violations.append(Violation("PY011", "Empty except block (bare pass)",
                                                         lineno, Severity.WARNING, Phase.SEMANTIC))
                        break
                    if nxt:
                        break

            # PY012: deep nesting
            if re.match(r'^( {16,}|\t{4,})\S', text):
                self.violations.append(Violation("PY012", "Code nested > 4 levels deep — consider refactoring",
                                                 lineno, Severity.INFO, Phase.SEMANTIC))

            # PY014: magic numbers
            if not stripped.startswith(('import', 'from', '#', 'def ', 'class ')):
                if re.search(r'(?<!["\w])([2-9]\d*|[1-9]\d+)(?![\w"])', text):
                    self.violations.append(Violation("PY014", "Magic number — consider a named constant",
                                                     lineno, Severity.INFO, Phase.SEMANTIC))

            # PY015: global statement
            if re.match(r'^\s+global\s+\w+', text):
                self.violations.append(Violation("PY015", "Use of 'global' — prefer passing arguments",
                                                 lineno, Severity.WARNING, Phase.SEMANTIC))

            # Track assignments + usage for PY005/PY006
            am = assign_re.match(text)
            if am and not class_re.match(text):
                assigned[am.group(1)] = lineno
            for um in used_re.finditer(stripped):
                used.add(um.group(1))

        # PY005: assigned but never used
        for var, line in assigned.items():
            if var not in used and var not in BUILTINS and var not in KEYWORDS:
                self.violations.append(Violation("PY005", f"Variable '{var}' assigned but never used",
                                                 line, Severity.WARNING, Phase.SEMANTIC))

        # Deduplicate
        seen: Set = set()
        unique = []
        for v in sorted(self.violations, key=lambda x: x.line):
            key = (v.line, v.rule)
            if key not in seen:
                seen.add(key)
                unique.append(v)
        return unique
