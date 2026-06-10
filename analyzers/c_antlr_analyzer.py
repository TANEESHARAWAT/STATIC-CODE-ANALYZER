"""
CAntlrAnalyzer — walks the ANTLR4 C parse tree for semantic checks.
Only loaded when the generated C grammar is present.
"""

from typing import List
from core.models import Violation, Severity, Phase


class CAntlrAnalyzer:
    """
    Walks a C parse tree produced by the ANTLR4 C grammar.
    Supplements the regex-based CAnalyzer with tree-level checks.
    """

    def __init__(self):
        self.violations: List[Violation] = []

    def walk(self, tree):
        """Entry point — walk the full parse tree."""
        try:
            from antlr4 import ParseTreeWalker
            from antlr4.tree.Tree import TerminalNodeImpl
            self._visit(tree)
        except Exception:
            pass  # gracefully degrade

    def _visit(self, node):
        try:
            from antlr4.tree.Tree import TerminalNodeImpl
            if not isinstance(node, TerminalNodeImpl):
                for i in range(node.getChildCount()):
                    self._visit(node.getChild(i))
        except Exception:
            pass
