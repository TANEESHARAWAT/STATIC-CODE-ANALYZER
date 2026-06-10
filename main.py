"""
Static Code Analyzer — Unified CLI Entry Point
Supports Python (.py) and C (.c / .h) files.

Usage:
    python main.py <file>                     Analyze file, plain-text output
    python main.py <file> --dashboard         Open HTML dashboard in browser
    python main.py <file> --format json       Output as JSON
    python main.py <file> --ai                Analyze + AI-powered fix suggestions
    python main.py <file> --ai --fix          Write AI-fixed code to <file>.fixed.c
    python main.py --generate "description"   Generate new C code using AI
    python main.py --help
"""

import sys
import os
import argparse
from typing import List

from core.models import Violation
from core.report import generate_report


SUPPORTED_EXTENSIONS = {
    ".py": "Python",
    ".c":  "C",
    ".h":  "C",
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Static Code Analyzer for Python and C — with AI-powered fixes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py samples/bad_code.c
  python main.py samples/bad_code.c --dashboard
  python main.py samples/bad_code.py --dashboard
  python main.py samples/bad_code.c --format json
  python main.py samples/bad_code.c --ai
  python main.py samples/bad_code.c --ai --fix
  python main.py --generate "a function that reads a file line by line"
        """
    )
    parser.add_argument(
        "filepath",
        nargs="?",
        help="Path to the source file to analyze (.py / .c / .h)"
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)"
    )
    parser.add_argument(
        "--dashboard",
        action="store_true",
        help="Generate an HTML dashboard and open it in the browser"
    )
    parser.add_argument(
        "--ai",
        action="store_true",
        help="Use AI to suggest fixes for all violations found"
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Write AI-fixed code to <filepath>.fixed.<ext> (requires --ai)"
    )
    parser.add_argument(
        "--generate",
        metavar="DESCRIPTION",
        help="Generate new C code from a natural language description using AI"
    )
    parser.add_argument(
        "--explain",
        action="store_true",
        help="Ask AI to explain each violation in plain English"
    )
    return parser.parse_args()


def get_analyzer(filepath: str):
    _, ext = os.path.splitext(filepath)
    ext = ext.lower()
    if ext == ".py":
        from core.runner import analyze_python
        return "Python", analyze_python
    elif ext in (".c", ".h"):
        from core.c_runner import analyze_c
        return "C", analyze_c
    else:
        supported = ", ".join(SUPPORTED_EXTENSIONS.keys())
        print(f"[ERROR] Unsupported file type '{ext}'. Supported: {supported}")
        sys.exit(1)


def run_ai_suggestions(filepath, source, violations, language, write_fix):
    from ai_suggester import suggest_fixes
    print("\n" + "=" * 60)
    print("  AI-POWERED FIX SUGGESTIONS")
    print("=" * 60)
    print("[AI] Sending code to Claude for analysis and fixes...")
    result = suggest_fixes(source, violations, language=language, filepath=filepath)
    print("\n[AI] EXPLANATION OF FIXES:")
    print("-" * 60)
    print(result["explanation"])
    if write_fix:
        base, ext = os.path.splitext(filepath)
        fixed_path = f"{base}.fixed{ext}"
        with open(fixed_path, "w", encoding="utf-8") as f:
            f.write(result["fixed_code"])
        print(f"\n[AI] Fixed code written to: {fixed_path}")
    else:
        print("\n[AI] CORRECTED CODE:")
        print("-" * 60)
        print(result["fixed_code"])


def run_explain(violations, language):
    from ai_suggester import explain_violation
    print("\n" + "=" * 60)
    print("  AI VIOLATION EXPLANATIONS")
    print("=" * 60)
    for v in sorted(violations, key=lambda x: x.line):
        print(f"\n{'─'*50}")
        print(f"  {v}")
        print(f"  Explanation: {explain_violation(v, language)}")


def run_generate(description):
    from ai_suggester import generate_code_from_description
    print("[AI] Generating C code from description...")
    print("=" * 60)
    code = generate_code_from_description(description, language="C")
    print(code)
    save_path = "generated_code.c"
    with open(save_path, "w", encoding="utf-8") as f:
        f.write(code)
    print(f"\n[AI] Code saved to: {save_path}")


def main():
    args = parse_args()

    if args.generate:
        run_generate(args.generate)
        return

    if not args.filepath:
        print("[ERROR] Please provide a file path. Use --help for usage.")
        sys.exit(1)

    filepath = args.filepath
    if not os.path.isfile(filepath):
        print(f"[ERROR] File not found: {filepath}")
        sys.exit(1)

    language, analyze_fn = get_analyzer(filepath)
    print(f"[INFO] Language detected: {language}")
    print(f"[INFO] Analyzing: {filepath}")

    violations = analyze_fn(filepath)

    # --dashboard mode
    if args.dashboard:
        from core.dashboard import generate_dashboard
        out_path = generate_dashboard(filepath, violations, open_browser=True)
        print(f"[INFO] Dashboard generated: {out_path}")
        print(f"[INFO] Opening in browser...")
        return

    # Normal terminal report
    generate_report(filepath, violations, fmt=args.format)

    if args.explain and violations:
        run_explain(violations, language)

    if args.ai:
        with open(filepath, encoding="utf-8", errors="replace") as f:
            source = f.read()
        run_ai_suggestions(filepath, source, violations, language, write_fix=args.fix)


if __name__ == "__main__":
    main()
