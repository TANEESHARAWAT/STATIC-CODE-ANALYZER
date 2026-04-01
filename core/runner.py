"""
Parses a source file and runs the appropriate analyzer visitor.

NOTE: Imports for generated lexers/parsers work only after you run the
antlr4 code generation step (see README or grammars/README.md).
"""

from typing import List
from core.models import Violation


def analyze_python(filepath: str) -> List[Violation]:
    """Parse a Python file and return all violations."""
    try:
        from antlr4 import FileStream, CommonTokenStream
        from generated.python3.Python3Lexer  import Python3Lexer
        from generated.python3.Python3Parser import Python3Parser
        from analyzers.python_analyzer import PythonAnalyzer

        input_stream = FileStream(filepath, encoding="utf-8")
        lexer        = Python3Lexer(input_stream)
        stream       = CommonTokenStream(lexer)
        parser       = Python3Parser(stream)
        tree         = parser.file_input()

        analyzer = PythonAnalyzer()
        analyzer.visit(tree)
        return analyzer.violations

    except ImportError:
        print("[ERROR] Generated Python parser not found.")
        print("        Run: antlr4 -Dlanguage=Python3 -visitor -o generated/python3 grammars/Python3.g4")
        return []


def analyze_java(filepath: str) -> List[Violation]:
    """Parse a Java file and return all violations."""
    try:
        from antlr4 import FileStream, CommonTokenStream
        from generated.java8.Java8Lexer  import Java8Lexer
        from generated.java8.Java8Parser import Java8Parser
        from analyzers.java_analyzer import JavaAnalyzer

        input_stream = FileStream(filepath, encoding="utf-8")
        lexer        = Java8Lexer(input_stream)
        stream       = CommonTokenStream(lexer)
        parser       = Java8Parser(stream)
        tree         = parser.compilationUnit()

        analyzer = JavaAnalyzer()
        analyzer.visit(tree)
        return analyzer.violations

    except ImportError:
        print("[ERROR] Generated Java parser not found.")
        print("        Run: antlr4 -Dlanguage=Python3 -visitor -o generated/java8 grammars/Java8.g4")
        return []
