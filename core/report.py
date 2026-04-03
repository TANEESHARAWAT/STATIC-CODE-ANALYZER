"""
Report generation for static analysis results.
"""

import json
from typing import List
from core.models import Violation


def print_text(filepath: str, violations: List[Violation]) -> None:
    print(f"\nAnalyzing: {filepath}")
    print("------------------------------------------------------------")
    if not violations:
        print("  No issues found.")
        return
    for v in sorted(violations, key=lambda x: x.line):
        print(f"  {v}")
    print(f"\n  Total: {len(violations)} issue(s) found.")


def print_json(filepath: str, violations: List[Violation]) -> None:
    output = {
        "file": filepath,
        "total": len(violations),
        "violations": [
            {
                "rule":     v.rule,
                "message":  v.message,
                "line":     v.line,
                "severity": v.severity.value,
            }
            for v in sorted(violations, key=lambda x: x.line)
        ],
    }
    print(json.dumps(output, indent=2))


def generate_report(filepath: str, violations: List[Violation], fmt: str = "text") -> None:
    if fmt == "json":
        print_json(filepath, violations)
    else:
        print_text(filepath, violations)
