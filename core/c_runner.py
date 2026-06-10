"""
C source file analyzer.
Uses ANTLR4 with a C grammar for lexical + syntax analysis,
then applies semantic checks on top.
Falls back to pure-regex if ANTLR4 is not installed.
"""

from typing import List, Tuple
from core.models import Violation, Phase, Severity


# ---------------------------------------------------------------------------
# ANTLR4 error listener — captures lex/parse errors with line + column
# ---------------------------------------------------------------------------

def _antlr_analyze(filepath: str) -> Tuple[List[Violation], bool]:
    """
    Try to parse with ANTLR4 C grammar.
    Returns (violations, success).
    """
    try:
        from antlr4 import FileStream, CommonTokenStream, DiagnosticErrorListener
        from antlr4.error.ErrorListener import ErrorListener
        from generated.c.CLexer import CLexer
        from generated.c.CParser import CParser
        from analyzers.c_antlr_analyzer import CAntlrAnalyzer

        class CollectingErrorListener(ErrorListener):
            def __init__(self):
                super().__init__()
                self.violations: List[Violation] = []

            def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
                # Classify as lexical or syntax
                phase = Phase.LEXICAL if "token recognition error" in str(msg).lower() else Phase.SYNTAX
                sev   = Severity.ERROR
                rule  = "LEX001" if phase == Phase.LEXICAL else "SYN001"
                self.violations.append(Violation(rule, msg, line, sev, phase, column))

        input_stream = FileStream(filepath, encoding="utf-8", errors="replace")
        lexer        = CLexer(input_stream)
        err_listener = CollectingErrorListener()
        lexer.removeErrorListeners()
        lexer.addErrorListener(err_listener)

        stream = CommonTokenStream(lexer)
        parser = CParser(stream)
        parser.removeErrorListeners()
        parser.addErrorListener(err_listener)

        tree = parser.compilationUnit()

        # Walk AST for semantic checks
        analyzer = CAntlrAnalyzer()
        analyzer.walk(tree)

        all_violations = err_listener.violations + analyzer.violations
        return all_violations, True

    except ImportError:
        return [], False


def analyze_c(filepath: str) -> List[Violation]:
    """
    Parse *filepath* as C source and return a list of Violation objects.
    Uses ANTLR4 if available, otherwise falls back to the regex analyzer.
    """
    try:
        with open(filepath, encoding="utf-8", errors="replace") as fh:
            source = fh.read()
    except FileNotFoundError:
        print(f"[ERROR] File not found: {filepath}")
        return []

    # Try ANTLR4 first
    antlr_violations, antlr_ok = _antlr_analyze(filepath)

    # Always run the deep regex/semantic analyzer
    from analyzers.c_analyzer import CAnalyzer
    regex_violations = CAnalyzer().analyze(source)

    if antlr_ok:
        # Merge: ANTLR gives us lex/syntax, regex gives us semantic
        # Deduplicate by (line, rule)
        seen = set()
        merged = []
        for v in antlr_violations + regex_violations:
            key = (v.line, v.rule)
            if key not in seen:
                seen.add(key)
                merged.append(v)
        return sorted(merged, key=lambda x: x.line)
    else:
        return sorted(regex_violations, key=lambda x: x.line)
