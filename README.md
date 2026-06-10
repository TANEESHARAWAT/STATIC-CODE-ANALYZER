# Static Code Analyzer — Python & C with AI-Powered Fixes

A compiler-inspired static analysis tool that checks **Python** and **C** source code across all four compiler phases, then uses **Claude AI** to suggest and generate fixed code.

---

## Features

| Feature | Python | C |
|---------|--------|---|
| ANTLR4 parsing | ✓ | ✓ (with grammar) |
| Lexical analysis | ✓ | ✓ |
| Syntax analysis | ✓ | ✓ |
| Semantic analysis | ✓ | ✓ |
| AI fix suggestions | ✓ | ✓ |

---

## Compiler Phases

The analyzer mirrors the stages of a real compiler:

1. **Lexical Analysis** — Tokenization errors: invalid escape sequences, unclosed strings/chars, bad literals
2. **Syntax Analysis** — Grammar errors: missing semicolons, unmatched brackets/braces/parens, malformed declarations
3. **Semantic Analysis** — Logic errors: undeclared variables, unused variables, unsafe functions, type issues, dead code
4. **Code Generation** — Hints: missing return paths, ignored return values, const suggestions

---

## Setup

### Requirements
- Python 3.8+
- pip

### Quick Install

```bash
bash setup.sh
```

Or manually:

```bash
python3 -m venv venv
source venv/bin/activate         # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

---

## Usage

### Analyze a C file
```bash
python main.py samples/bad_code.c
```

### Analyze a Python file
```bash
python main.py samples/bad_code.py
```

### JSON output
```bash
python main.py samples/bad_code.c --format json
```

### Write AI-fixed code to a new file
```bash
python main.py samples/bad_code.c --ai --fix
# Creates: samples/bad_code.fixed.c
```

### AI explanation of each violation
```bash
python main.py samples/bad_code.c --explain
```

---

## C Rules Reference

### Lexical (LEX)
| Rule | Severity | Description |
|------|----------|-------------|
| LEX002 | WARNING | Invalid escape sequence in string/char literal |
| LEX003 | ERROR | Unclosed string literal |
| LEX004 | ERROR | Unclosed character literal |
| LEX005 | WARNING | Multi-character character literal |

### Syntax (SYN)
| Rule | Severity | Description |
|------|----------|-------------|
| SYN002 | ERROR | Missing semicolon at end of statement |
| SYN003 | ERROR | Unmatched opening brace `{` |
| SYN004 | ERROR | Unmatched closing brace `}` |
| SYN005 | ERROR | Unmatched opening parenthesis `(` |
| SYN006 | ERROR | Unmatched closing parenthesis `)` |
| SYN007 | ERROR | Unmatched opening bracket `[` |
| SYN008 | ERROR | Unmatched closing bracket `]` |
| SYN009 | WARNING | Empty function body |
| SYN010 | ERROR | `else` without matching `if` |
| SYN011 | ERROR | Unclosed block comment |

### Semantic (SEM)
| Rule | Severity | Description |
|------|----------|-------------|
| SEM001 | WARNING | Function name not snake_case |
| SEM002 | WARNING | Too many parameters (> 5) |
| SEM003 | ERROR | Use of `gets()` — buffer overflow risk |
| SEM004 | WARNING | Use of `strcpy()` — unsafe |
| SEM005 | INFO | Magic number literal |
| SEM006 | WARNING | Variable declared but never used |
| SEM007 | WARNING | Non-void function with no return statement |
| SEM008 | INFO | Empty else block |
| SEM009 | ERROR | `scanf()` with `%s` and no field-width limit |
| SEM010 | WARNING | `malloc`/`calloc`/`realloc` result not checked for NULL |
| SEM011 | ERROR | Identifier used but not declared |
| SEM012 | ERROR | Division by zero (literal) |
| SEM013 | WARNING | Assignment `=` inside condition (probably meant `==`) |
| SEM014 | ERROR | `printf` with non-literal format string (injection risk) |
| SEM015 | WARNING | Dead code after `return`/`break`/`continue` |
| SEM016 | ERROR | Array index out of bounds (literal index) |
| SEM017 | WARNING | Infinite loop with no `break` or `return` |
| SEM018 | WARNING | Dangerous/deprecated function (`sprintf`, `strcat`, `strtok`) |
| SEM019 | WARNING | Variable shadowing outer-scope declaration |
| SEM020 | WARNING | Standard function used without including its header |
| SEM021 | WARNING | Signed/unsigned comparison |
| SEM022 | WARNING | Function called before it is declared |
| SEM023 | WARNING | Pointer arithmetic on `void*` |
| SEM024 | ERROR | Potential double-free |
| SEM025 | INFO | Global variable mutated inside function |

### Code Generation (CGN)
| Rule | Severity | Description |
|------|----------|-------------|
| CGN001 | WARNING | Not all code paths return a value |
| CGN002 | WARNING | Return value of critical function ignored |
| CGN003 | INFO | Pointer parameter could be `const` |

---

## Python Rules Reference

| Rule | Severity | Description |
|------|----------|-------------|
| PY001 | WARNING | Function name not snake_case |
| PY002 | WARNING | Too many parameters (> 5) |
| PY003 | ERROR | Bare `except:` clause |
| PY005 | WARNING | Variable assigned but never used |
| PY006 | WARNING | Variable used but never defined |

---

## Project Structure

```
static-analyzer/
├── main.py                     ← Unified CLI entry point
├── ai_suggester.py             ← AI fix/generation via Anthropic API
├── requirements.txt
├── setup.sh
│
├── analyzers/
│   ├── c_analyzer.py           ← 35+ C rules (all phases)
│   ├── c_antlr_analyzer.py     ← ANTLR4 AST walker for C
│   └── python_analyzer.py      ← ANTLR4 visitor for Python
│
├── core/
│   ├── models.py               ← Violation, Severity, Phase
│   ├── runner.py               ← Python analysis runner
│   ├── c_runner.py             ← C analysis runner
│   └── report.py               ← Text/JSON report output
│
├── generated/
│   └── python3/                ← Pre-generated ANTLR4 Python grammar
│
├── grammars/
│   ├── Python3Lexer.g4
│   └── Python3Parser.g4
│
├── samples/
│   ├── bad_code.c              ← C file with violations across all phases
│   └── bad_code.py             ← Python file with violations
│
├── tests/
│   ├── test_c_rules.py
│   └── test_python_rules.py
│
└── docs/
    └── rules.md
```

---

## Running Tests

```bash
python -m pytest tests/ -v
# or
python -m unittest discover tests/
```

---

## How to Add a New C Rule

1. Open `analyzers/c_analyzer.py`
2. Add a new function `_check_semXXX(lines, source) -> List[Violation]`
3. Append it to the `CHECKS` list at the bottom
4. Add a test in `tests/test_c_rules.py`
