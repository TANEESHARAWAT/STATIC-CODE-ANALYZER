"""
Python analysis runner.
Uses ANTLR4 if installed, falls back to regex analyzer otherwise.
"""

from typing import List
from core.models import Violation


def analyze_python(filepath: str) -> List[Violation]:
    try:
        with open(filepath, encoding="utf-8", errors="replace") as f:
            source = f.read()
    except FileNotFoundError:
        print(f"[ERROR] File not found: {filepath}")
        return []

    # Try ANTLR4 first
    antlr_violations, antlr_ok = _antlr_analyze(filepath, source)

    # Always run regex analyzer
    from analyzers.python_antlr_analyzer import PythonAntlrAnalyzer
    regex_violations = PythonAntlrAnalyzer().regex_only(source)

    if antlr_ok:
        all_v = antlr_violations + regex_violations
    else:
        all_v = regex_violations

    seen, merged = set(), []
    for v in sorted(all_v, key=lambda x: x.line):
        key = (v.line, v.rule)
        if key not in seen:
            seen.add(key)
            merged.append(v)
    return merged


def _antlr_analyze(filepath: str, source: str):
    try:
        from antlr4 import FileStream, CommonTokenStream
        from antlr4.error.ErrorListener import ErrorListener
        from generated.python3.Python3Lexer  import Python3Lexer
        from generated.python3.Python3Parser import Python3Parser
        from analyzers.python_antlr_analyzer import PythonAntlrAnalyzer
        from core.models import Severity, Phase

        class CollectingErrorListener(ErrorListener):
            def __init__(self):
                super().__init__()
                self.violations = []
            def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
                phase = Phase.LEXICAL if "token recognition" in str(msg).lower() else Phase.SYNTAX
                rule  = "LEX001" if phase == Phase.LEXICAL else "SYN001"
                self.violations.append(Violation(rule, msg, line, Severity.ERROR, phase, column))

        input_stream = FileStream(filepath, encoding="utf-8")
        lexer  = Python3Lexer(input_stream)
        err_listener = CollectingErrorListener()
        lexer.removeErrorListeners()
        lexer.addErrorListener(err_listener)

        stream = CommonTokenStream(lexer)
        parser = Python3Parser(stream)
        parser.removeErrorListeners()
        parser.addErrorListener(err_listener)

        tree = parser.file_input()

        analyzer   = PythonAntlrAnalyzer()
        violations = analyzer.analyze_tree(tree, source)

        return err_listener.violations + violations, True

    except ImportError:
        return [], False
