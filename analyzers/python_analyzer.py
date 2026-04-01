"""
Python 3 static analysis rules.

Each visitXxx method corresponds to a grammar rule in Python3.g4.
Add new rules by overriding more visitXxx methods.

Rules implemented:
  PY001 - Function name not snake_case
  PY002 - Too many parameters (> 5)
  PY003 - Bare except clause
  PY004 - Ambiguous variable name (l, O, I)
"""

import re
from typing import List
from core.models import Violation, Severity

try:
    from generated.python3.Python3Visitor import Python3Visitor
    BASE = Python3Visitor
except ImportError:
    BASE = object  # fallback so the file is importable before generation


class PythonAnalyzer(BASE):

    def __init__(self):
        self.violations: List[Violation] = []

    def _add(self, rule: str, message: str, line: int, severity: Severity = Severity.WARNING):
        self.violations.append(Violation(rule, message, line, severity))

    # ── PY001: snake_case function names ──────────────────────────────────
    def visitFuncdef(self, ctx):
        name = ctx.NAME().getText()
        if not re.match(r'^[a-z_][a-z0-9_]*$', name):
            self._add(
                "PY001",
                f"Function '{name}' should use snake_case naming",
                ctx.start.line,
            )
        return self.visitChildren(ctx)

    # ── PY002: too many parameters ────────────────────────────────────────
    def visitTypedargslist(self, ctx):
        params = [c for c in ctx.children if hasattr(c, 'getText') and c.getText() != ',']
        if len(params) > 5:
            self._add(
                "PY002",
                f"Function has {len(params)} parameters (max recommended: 5)",
                ctx.start.line,
            )
        return self.visitChildren(ctx)

    # ── PY003: bare except ────────────────────────────────────────────────
    def visitExcept_clause(self, ctx):
        if ctx.getChildCount() == 1:  # only the 'except' keyword, no type
            self._add(
                "PY003",
                "Bare 'except:' catches all exceptions — specify an exception type",
                ctx.start.line,
                Severity.ERROR,
            )
        return self.visitChildren(ctx)

    # ── PY004: ambiguous variable names ───────────────────────────────────
    def visitExpr_stmt(self, ctx):
        text = ctx.start.text
        if text in ('l', 'O', 'I'):
            self._add(
                "PY004",
                f"Ambiguous variable name '{text}' (looks like 1, 0, or 1)",
                ctx.start.line,
            )
        return self.visitChildren(ctx)

    # ── default: walk all children ────────────────────────────────────────
    def visitChildren(self, node):
        for i in range(node.getChildCount()):
            self.visit(node.getChild(i))
        return None
