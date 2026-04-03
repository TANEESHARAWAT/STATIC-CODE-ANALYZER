"""
Parses a Python source file and runs the PythonAnalyzer visitor using ANTLR4.
"""

from typing import List
from core.models import Violation


def analyze_python(filepath: str) -> List[Violation]:
    try:
        from antlr4 import FileStream, CommonTokenStream
        from generated.python3.Python3Lexer  import Python3Lexer
        from generated.python3.Python3Parser import Python3Parser
        from analyzers.python_analyzer import PythonAnalyzer

        input_stream = FileStream(filepath, encoding="utf-8")
        lexer        = Python3Lexer(input_stream)
        stream       = CommonTokenStream(lexer)
        parser       = Python3Parser(stream)
        parser.removeErrorListeners()

        tree = parser.file_input()

        analyzer = PythonAnalyzer()
        analyzer.visit(tree)   # ✅ CORRECT

        return analyzer.violations

    except ImportError as e:
        print(f"[ERROR] Required module not found: {e}")
        print("        Run: pip install -r requirements.txt")
        return []
