"""
Data models used across the analyzer.
"""

from dataclasses import dataclass
from enum import Enum


class Severity(Enum):
    ERROR   = "ERROR"
    WARNING = "WARNING"
    INFO    = "INFO"


@dataclass
class Violation:
    rule:     str
    message:  str
    line:     int
    severity: Severity = Severity.WARNING

    def __str__(self) -> str:
        return f"[{self.severity.value}] Line {self.line} | {self.rule}: {self.message}"
