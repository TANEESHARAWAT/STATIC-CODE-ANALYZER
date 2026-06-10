"""
_PythonVisitor — internal ANTLR4 tree visitor for Python.
Used by PythonAntlrAnalyzer. Not imported directly from outside.
"""

import re
from typing import Dict
from core.models import Violation, Severity, Phase

BUILTINS = {
    "print","len","range","int","str","float","bool","list","dict","set",
    "tuple","type","isinstance","hasattr","getattr","setattr","enumerate",
    "zip","map","filter","sorted","reversed","sum","min","max","abs",
    "round","open","input","super","object","None","True","False",
    "self","cls",
}

KEYWORDS = {
    "and","as","assert","async","await","break","class","continue","def",
    "del","elif","else","except","finally","for","from","global","if",
    "import","in","is","lambda","nonlocal","not","or","pass","raise",
    "return","try","while","with","yield",
}


class _PythonVisitor:
    def __init__(self, analyzer):
        self.analyzer = analyzer
        self.violations = analyzer.violations
        self.assigned_vars: Dict[str, int] = {}
        self.used_vars: Dict[str, int] = {}

    def _add(self, rule, msg, line, sev=Severity.WARNING, phase=Phase.SEMANTIC):
        self.violations.append(Violation(rule, msg, line, sev, phase))

    def visit(self, tree):
        self._walk(tree)

    def _walk(self, node):
        try:
            from antlr4 import TerminalNode
            from generated.python3.Python3Parser import Python3Parser

            if isinstance(node, TerminalNode):
                return

            rule = node.getRuleIndex() if hasattr(node, 'getRuleIndex') else -1

            # PY001 + PY002: function definition
            if rule == Python3Parser.RULE_funcdef:
                self._visit_funcdef(node)

            # PY003: bare except
            elif rule == Python3Parser.RULE_except_clause:
                if node.getChildCount() == 1:
                    self._add("PY003", "Bare 'except:' catches all exceptions — specify exception type",
                              node.start.line, Severity.ERROR)

            # Variable assignment tracking
            elif rule == Python3Parser.RULE_expr_stmt:
                self._visit_expr_stmt(node)

            # Usage in return
            elif rule == Python3Parser.RULE_return_stmt:
                self._track_usage(node)

            # Usage in if/while/for conditions
            elif rule in (Python3Parser.RULE_if_stmt,
                          Python3Parser.RULE_while_stmt,
                          Python3Parser.RULE_for_stmt):
                self._track_usage(node)

            for i in range(node.getChildCount()):
                self._walk(node.getChild(i))

        except Exception:
            pass

    def _visit_funcdef(self, ctx):
        from generated.python3.Python3Parser import Python3Parser
        from antlr4 import TerminalNode

        try:
            name = ctx.NAME().getText()
        except Exception:
            return

        # PY001: snake_case
        if not re.match(r'^[a-z_][a-z0-9_]*$', name):
            self._add("PY001", f"Function '{name}' should use snake_case", ctx.start.line)

        # PY002: param count
        try:
            params_ctx = ctx.parameters()
            if params_ctx:
                typed = params_ctx.typedargslist()
                if typed:
                    count = sum(
                        1 for c in typed.children
                        if hasattr(c, 'getRuleIndex') and
                           c.getRuleIndex() == Python3Parser.RULE_tfpdef
                    )
                    bare = sum(
                        1 for c in typed.children
                        if isinstance(c, TerminalNode) and
                           c.symbol.type == Python3Parser.NAME
                    )
                    total = count + bare
                    if total > 5:
                        self._add("PY002", f"Function '{name}' has {total} parameters (max 5)",
                                  ctx.start.line)
                    # Register params as assigned
                    for c in (typed.children or []):
                        if isinstance(c, TerminalNode) and c.symbol.type == Python3Parser.NAME:
                            self.assigned_vars[c.getText()] = ctx.start.line
        except Exception:
            pass

    def _visit_expr_stmt(self, ctx):
        from generated.python3.Python3Parser import Python3Parser
        from antlr4 import TerminalNode

        text = ctx.getText()
        if '=' not in text:
            self._track_usage(ctx)
            return

        lhs = ctx.getChild(0)

        def extract_names(node):
            names = []
            if isinstance(node, TerminalNode):
                if node.symbol.type == Python3Parser.NAME:
                    names.append((node.getText(), node.symbol.line))
            else:
                for i in range(node.getChildCount()):
                    names.extend(extract_names(node.getChild(i)))
            return names

        for var_name, line in extract_names(lhs):
            self.assigned_vars[var_name] = line

        # Track RHS usage
        def walk_rhs(node, skip):
            if node is skip:
                return
            if isinstance(node, TerminalNode):
                if node.symbol.type == Python3Parser.NAME:
                    n = node.getText()
                    if n not in BUILTINS and n not in KEYWORDS:
                        self.used_vars[n] = node.symbol.line
            else:
                for i in range(node.getChildCount()):
                    walk_rhs(node.getChild(i), skip)

        for i in range(1, ctx.getChildCount()):
            walk_rhs(ctx.getChild(i), None)

    def _track_usage(self, node):
        from generated.python3.Python3Parser import Python3Parser
        from antlr4 import TerminalNode

        def walk(n):
            if isinstance(n, TerminalNode):
                if n.symbol.type == Python3Parser.NAME:
                    name = n.getText()
                    if name not in BUILTINS and name not in KEYWORDS:
                        self.used_vars[name] = n.symbol.line
            else:
                for i in range(n.getChildCount()):
                    walk(n.getChild(i))
        walk(node)
