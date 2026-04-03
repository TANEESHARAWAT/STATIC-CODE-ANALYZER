"""
Python 3 static analysis rules using ANTLR4 Visitor pattern.

Rules implemented:
  PY001 - Function name not snake_case
  PY002 - Too many parameters (> 5)
  PY003 - Bare except clause
  PY004 - Ambiguous variable name (l, O, I)
"""

import re
from typing import List
from core.models import Violation, Severity
from generated.python3.Python3Visitor import Python3Visitor
from generated.python3.Python3Parser import Python3Parser

AMBIGUOUS_NAMES = {'l', 'O', 'I'}
BUILTINS = {"print", "len", "range"}


class PythonAnalyzer(Python3Visitor):

    def __init__(self):
        self.violations: List[Violation] = []
        self.assigned_vars = {}   # var_name -> line
        self.used_vars = {}       # var_name -> line

    def _add(self, rule: str, message: str, line: int, severity: Severity = Severity.WARNING):
        self.violations.append(Violation(rule, message, line, severity))

    # -------------------------------
    # PY001 + PARAMETER FIX (ANTLR WAY)
    # -------------------------------
    def visitFuncdef(self, ctx):
        name = ctx.name().getText()

        # PY001: naming
        if not re.match(r'^[a-z_][a-z0-9_]*$', name):
            self._add("PY001", f"Function '{name}' should use snake_case", ctx.start.line)

        # ✅ PROPER ANTLR PARAM EXTRACTION
        params_ctx = ctx.parameters()

        if params_ctx:
            typed_args = params_ctx.typedargslist()

            if typed_args:
                for child in typed_args.getChildren():
                    try:
                        # tfpdef → NAME
                        if child.getRuleIndex() == Python3Parser.RULE_tfpdef:
                            param_name = child.getChild(0).getText()
                            self.assigned_vars[param_name] = ctx.start.line
                    except:
                        pass

        return super().visitChildren(ctx)

    # -------------------------------
    # PY002: Too many parameters
    # -------------------------------
    def visitTypedargslist(self, ctx):
        params = [
            c for c in ctx.children
            if hasattr(c, 'getRuleIndex') and c.getRuleIndex() == Python3Parser.RULE_tfpdef
        ]

        from antlr4 import TerminalNode
        bare_name_params = [
            c for c in ctx.children
            if isinstance(c, TerminalNode)
            and c.symbol.type == Python3Parser.NAME
        ]

        total = len(params) + len(bare_name_params)

        if total > 5:
            self._add("PY002", f"Function has {total} parameters (max 5)", ctx.start.line)

        return super().visitChildren(ctx)

    # -------------------------------
    # PY003: Bare except
    # -------------------------------
    def visitExcept_clause(self, ctx):
        if ctx.getChildCount() == 1:
            self._add("PY003", "Bare 'except:' catches all exceptions", ctx.start.line, Severity.ERROR)
        return super().visitChildren(ctx)

    # -------------------------------
    # PY004 + Variable tracking
    # -------------------------------
    def visitExpr_stmt(self, ctx):
        from antlr4 import TerminalNode

        lhs_node = None

        # Detect assignment
        if "=" in ctx.getText():
            lhs_node = ctx.getChild(0)

            def extract_names(node):
                names = []
                if isinstance(node, TerminalNode):
                    if node.symbol.type == Python3Parser.NAME:
                        names.append(node.getText())
                else:
                    for i in range(node.getChildCount()):
                        names.extend(extract_names(node.getChild(i)))
                return names

            for var_name in extract_names(lhs_node):
                self.assigned_vars[var_name] = ctx.start.line

                if var_name in AMBIGUOUS_NAMES:
                    self._add("PY004", f"Ambiguous variable name '{var_name}'", ctx.start.line)

        # Track usage
        def walk(node):
            if node == lhs_node:
                return

            if isinstance(node, TerminalNode):
                if node.symbol.type == Python3Parser.NAME:
                    name = node.getText()

                    if name not in BUILTINS:
                        self.used_vars[name] = node.symbol.line

                    if name in AMBIGUOUS_NAMES:
                        self._add("PY004", f"Ambiguous variable name '{name}'", node.symbol.line)
            else:
                for i in range(node.getChildCount()):
                    walk(node.getChild(i))

        walk(ctx)
        return None

    # -------------------------------
    # Track usage in return
    # -------------------------------
    def visitReturn_stmt(self, ctx):
        from antlr4 import TerminalNode

        def walk(node):
            if isinstance(node, TerminalNode):
                if node.symbol.type == Python3Parser.NAME:
                    name = node.getText()
                    if name not in BUILTINS:
                        self.used_vars[name] = node.symbol.line
            else:
                for i in range(node.getChildCount()):
                    walk(node.getChild(i))

        walk(ctx)
        return None

    # -------------------------------
    # PY005: Unused variable
    # -------------------------------
    def check_unused_variables(self):
        for var, line in self.assigned_vars.items():
            if var not in self.used_vars:
                self._add("PY005", f"Variable '{var}' assigned but never used", line)

    # -------------------------------
    # PY006: Undefined variable
    # -------------------------------
    def check_undefined_variables(self):
        for var, line in self.used_vars.items():
            if var not in self.assigned_vars and var not in BUILTINS:
                self._add("PY006", f"Variable '{var}' used but never defined", line)