# Static Code Analyzer (Python)

A static code analyzer for **Python 3** built with [ANTLR4](https://www.antlr.org/).
Parses source files, walks the AST, and reports rule violations with line numbers and severity levels.

## Features
- Supports Python 3 source files (`.py`)
- Rule-based analysis using the ANTLR4 Visitor pattern
- Severity levels: `ERROR` / `WARNING` / `INFO`
- Output formats: plain text, JSON
- Clean CLI interface

## Project Structure
```
static-analyzer/
├── grammars/               # Python3 .g4 grammar files
├── generated/              # Pre-generated ANTLR4 parser — do not edit
│   └── python3/
├── analyzers/              # Visitor class with rule logic
│   └── python_analyzer.py
├── core/                   # Runner, report builder, violation model
│   ├── models.py
│   ├── report.py
│   └── runner.py
├── samples/                # Sample .py file with intentional violations
│   └── bad_code.py
├── tests/
│   └── test_python_rules.py
├── docs/
│   └── rules.md
├── main.py
└── requirements.txt
```

## Setup

### 1. (Optional but recommended) Create a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

## Usage
```bash
python main.py samples/bad_code.py
python main.py samples/bad_code.py --format json
python main.py path/to/your_file.py
```

## Rules

See [docs/rules.md](docs/rules.md) for the full reference.

| ID    | Language | Severity | Description                       |
|-------|----------|----------|-----------------------------------|
| PY001 | Python   | WARNING  | Function name not snake_case      |
| PY002 | Python   | WARNING  | Too many parameters (> 5)         |
| PY003 | Python   | ERROR    | Bare except clause                |
| PY004 | Python   | WARNING  | Ambiguous variable name           |

## Running Tests
```bash
python -m unittest discover tests/
```
