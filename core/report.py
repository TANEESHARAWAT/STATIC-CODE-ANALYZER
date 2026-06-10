"""
Report generation for static analysis results.
Supports text and JSON output with compiler phase information.
"""

import json
from typing import List
from core.models import Violation


def print_text(filepath: str, violations: List[Violation]) -> None:
    print(f"\nAnalyzing: {filepath}")
    print("=" * 70)
    if not violations:
        print("  ✓ No issues found. Code looks clean!")
        return

    # Group by phase
    from collections import defaultdict
    by_phase = defaultdict(list)
    for v in sorted(violations, key=lambda x: x.line):
        by_phase[v.phase.value].append(v)

    for phase_name in ["Lexical", "Syntax", "Semantic", "CodeGen"]:
        phase_violations = by_phase.get(phase_name, [])
        if not phase_violations:
            continue
        print(f"\n  ── {phase_name} Analysis ──────────────────────────────")
        for v in phase_violations:
            col_part = f":{v.column}" if v.column is not None else ""
            sev_icon = {"ERROR": "✗", "WARNING": "⚠", "INFO": "ℹ"}.get(v.severity.value, "·")
            print(f"  {sev_icon} Line {v.line}{col_part}  [{v.rule}]  {v.message}")

    errors   = sum(1 for v in violations if v.severity.value == "ERROR")
    warnings = sum(1 for v in violations if v.severity.value == "WARNING")
    infos    = sum(1 for v in violations if v.severity.value == "INFO")

    print(f"\n{'=' * 70}")
    print(f"  Total: {len(violations)} issue(s)  —  "
          f"{errors} error(s), {warnings} warning(s), {infos} info(s)")


def print_json(filepath: str, violations: List[Violation]) -> None:
    output = {
        "file":  filepath,
        "total": len(violations),
        "summary": {
            "errors":   sum(1 for v in violations if v.severity.value == "ERROR"),
            "warnings": sum(1 for v in violations if v.severity.value == "WARNING"),
            "infos":    sum(1 for v in violations if v.severity.value == "INFO"),
        },
        "violations": [
            {
                "rule":     v.rule,
                "message":  v.message,
                "line":     v.line,
                "column":   v.column,
                "severity": v.severity.value,
                "phase":    v.phase.value,
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
