"""
Static Code Analyzer — CLI entry point

Usage:
    python main.py <file>                  Analyze file, plain text output
    python main.py <file> --format json    Output as JSON
    python main.py --help
"""

import sys
import argparse
from core.runner  import analyze_python, analyze_java
from core.report  import generate_report


SUPPORTED = {".py": analyze_python, ".java": analyze_java}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Static Code Analyzer for Python and Java using ANTLR4"
    )
    parser.add_argument("filepath", help="Path to the source file to analyze")
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

    ext = "." + filepath.rsplit(".", 1)[-1] if "." in filepath else ""
    if ext not in SUPPORTED:
        print(f"[ERROR] Unsupported file type '{ext}'. Supported: {', '.join(SUPPORTED)}")
        sys.exit(1)

    violations = SUPPORTED[ext](filepath)
    generate_report(filepath, violations, fmt=args.format)


if __name__ == "__main__":
    main()
