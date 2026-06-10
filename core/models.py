"""
Data models used across the analyzer.
Includes compiler phases: Lexical, Syntax, Semantic, Code Generation.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Severity(Enum):
    ERROR   = "ERROR"
    WARNING = "WARNING"
    INFO    = "INFO"


class Phase(Enum):
    LEXICAL     = "Lexical"       # tokenization errors
    SYNTAX      = "Syntax"        # grammar / parse errors
    SEMANTIC    = "Semantic"      # type / scope / logic errors
    CODEGEN     = "CodeGen"       # code-generation hints


@dataclass
class Violation:
    rule:     str
    message:  str
    line:     int
    severity: Severity       = Severity.WARNING
    phase:    Phase          = Phase.SEMANTIC
    column:   Optional[int]  = None

    def __str__(self) -> str:
        col_part = f":{self.column}" if self.column is not None else ""
        return (
            f"[{self.severity.value}] [{self.phase.value}] "
            f"Line {self.line}{col_part} | {self.rule}: {self.message}"
        )
