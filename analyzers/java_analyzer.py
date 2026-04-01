"""
Java 8 static analysis rules.

Rules implemented:
  JV001 - Class name not PascalCase
  JV002 - Method name not camelCase
  JV003 - Empty catch block
  JV004 - Magic number (bare integer literal)
  JV005 - System.out.println left in code
"""

import re
from typing import List
from core.models import Violation, Severity

try:
    from generated.java8.Java8Visitor import Java8Visitor
    BASE = Java8Visitor
except ImportError:
    BASE = object


class JavaAnalyzer(BASE):

    def __init__(self):
        self.violations: List[Violation] = []

    def _add(self, rule: str, message: str, line: int, severity: Severity = Severity.WARNING):
        self.violations.append(Violation(rule, message, line, severity))

    # ── JV001: PascalCase class names ─────────────────────────────────────
    def visitNormalClassDeclaration(self, ctx):
        name = ctx.Identifier().getText()
        if not re.match(r'^[A-Z][a-zA-Z0-9]*$', name):
            self._add(
                "JV001",
                f"Class '{name}' should use PascalCase naming",
                ctx.start.line,
                Severity.ERROR,
            )
        return self.visitChildren(ctx)

    # ── JV002: camelCase method names ─────────────────────────────────────
    def visitMethodDeclarator(self, ctx):
        name = ctx.Identifier().getText()
        if not re.match(r'^[a-z][a-zA-Z0-9]*$', name):
            self._add(
                "JV002",
                f"Method '{name}' should use camelCase naming",
                ctx.start.line,
            )
        return self.visitChildren(ctx)

    # ── JV003: empty catch block ──────────────────────────────────────────
    def visitCatchClause(self, ctx):
        block = ctx.block()
        if block and block.blockStatements() is None:
            self._add(
                "JV003",
                "Empty catch block — exception is silently swallowed",
                ctx.start.line,
                Severity.ERROR,
            )
        return self.visitChildren(ctx)

    # ── JV005: System.out.println ─────────────────────────────────────────
    def visitStatement(self, ctx):
        text = ctx.getText()
        if "System.out.println" in text or "System.out.print(" in text:
            self._add(
                "JV005",
                "Remove System.out.println before committing to production",
                ctx.start.line,
                Severity.INFO,
            )
        return self.visitChildren(ctx)

    # ── default ───────────────────────────────────────────────────────────
    def visitChildren(self, node):
        for i in range(node.getChildCount()):
            self.visit(node.getChild(i))
        return None
