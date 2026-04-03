"""
Static Code Analyzer — CLI entry point  (Python only)

Usage:
    python main.py <file.py>                  Analyze file, plain text output
    python main.py <file.py> --format json    Output as JSON
    python main.py --help
"""

import sys
import argparse
from core.runner import analyze_python
from core.report import generate_report


def parse_args():
    parser = argparse.ArgumentParser(
        description="Static Code Analyzer for Python using ANTLR4"
    )
    parser.add_argument("filepath", help="Path to the .py source file to analyze")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    filepath = args.filepath

    if not filepath.endswith(".py"):
        print(f"[ERROR] Unsupported file type. This analyzer supports .py files only.")
        sys.exit(1)

    violations = analyze_python(filepath)
    generate_report(filepath, violations, fmt=args.format)


if __name__ == "__main__":
    main()
