"""
C Static Analyzer — Comprehensive rule checker for .c / .h files.

Compiler Phase Coverage
------------------------
LEXICAL  (LEX*): unrecognized tokens, invalid escape sequences, unclosed strings/chars
SYNTAX   (SYN*): missing semicolons, unmatched brackets/braces/parens, malformed declarations
SEMANTIC (SEM*): undeclared variables, type mismatches, unused vars, unreachable code, etc.
CODEGEN  (CGN*): code-generation hints (missing return, always-true conditions, etc.)

Full Rule List
--------------
LEX001  Token recognition error (ANTLR)
LEX002  Invalid escape sequence in string/char literal
LEX003  Unclosed string literal
LEX004  Unclosed character literal
LEX005  Multi-character character literal

SYN001  General syntax error (ANTLR)
SYN002  Missing semicolon at end of statement
SYN003  Unmatched opening brace {
SYN004  Unmatched closing brace }
SYN005  Unmatched opening parenthesis (
SYN006  Unmatched closing parenthesis )
SYN007  Unmatched opening bracket [
SYN008  Unmatched closing bracket ]
SYN009  Empty function body warning
SYN010  else without matching if
SYN011  Missing closing comment */

SEM001  Function name not snake_case
SEM002  Too many parameters (> 5)
SEM003  Use of gets() — unsafe
SEM004  Use of strcpy() — unsafe
SEM005  Magic number literal
SEM006  Variable declared but never used
SEM007  Missing return in non-void function
SEM008  Empty else block
SEM009  scanf without field-width limit
SEM010  malloc/calloc/realloc result not checked for NULL
SEM011  Undeclared variable used
SEM012  Division by zero (literal)
SEM013  Comparison with = instead of ==
SEM014  Use of printf without format string (format injection)
SEM015  Dead code after return/break/continue
SEM016  Array index out of bounds (literal index vs declared size)
SEM017  Infinite loop — while(1) or for(;;) without break
SEM018  Use of deprecated/dangerous function (sprintf, strcat, strtok)
SEM019  Variable shadowing (inner scope redefines outer scope name)
SEM020  Missing #include for used standard functions
SEM021  Signed/unsigned comparison
SEM022  Implicit function declaration (called before defined/declared)
SEM023  Pointer arithmetic on void*
SEM024  Double free / use-after-free pattern
SEM025  Global variable mutated inside function (side-effect warning)

CGN001  Non-void function has no return path
CGN002  Function with output parameter but no return value check
CGN003  Suggest const for pointer parameter not modified
"""

import re
from typing import List, Dict, Set, Tuple, Optional
from core.models import Violation, Severity, Phase


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _lines(source: str) -> List[Tuple[int, str]]:
    return list(enumerate(source.splitlines(), start=1))


def _strip_strings(source: str) -> str:
    """Replace string/char literal contents with spaces (preserves line count)."""
    result = re.sub(r'"(?:[^"\\]|\\.)*"', lambda m: '"' + ' ' * (len(m.group()) - 2) + '"', source)
    result = re.sub(r"'(?:[^'\\]|\\.)*'", lambda m: "'" + ' ' * (len(m.group()) - 2) + "'", result)
    return result


def _strip_comments(source: str) -> str:
    """Remove C block- and line-comments (preserves line numbers)."""
    source = re.sub(r'/\*.*?\*/', lambda m: '\n' * m.group().count('\n'), source, flags=re.DOTALL)
    source = re.sub(r'//[^\n]*', '', source)
    return source


def _strip_preprocessor(source: str) -> str:
    return re.sub(r'^\s*#[^\n]*', '', source, flags=re.MULTILINE)


C_KEYWORDS = {
    'auto', 'break', 'case', 'char', 'const', 'continue', 'default',
    'do', 'double', 'else', 'enum', 'extern', 'float', 'for', 'goto',
    'if', 'inline', 'int', 'long', 'register', 'restrict', 'return',
    'short', 'signed', 'sizeof', 'static', 'struct', 'switch', 'typedef',
    'union', 'unsigned', 'void', 'volatile', 'while',
    'NULL', 'true', 'false', 'bool', 'size_t', 'ssize_t',
    'uint8_t', 'uint16_t', 'uint32_t', 'uint64_t',
    'int8_t', 'int16_t', 'int32_t', 'int64_t',
    'ptrdiff_t', 'intptr_t', 'uintptr_t',
    'FILE', 'EOF',
}

C_TYPE_KEYWORDS = {
    'int', 'char', 'float', 'double', 'long', 'short',
    'unsigned', 'signed', 'void', 'size_t', 'ssize_t',
    'uint8_t', 'uint16_t', 'uint32_t', 'uint64_t',
    'int8_t', 'int16_t', 'int32_t', 'int64_t',
    'bool', '_Bool', 'ptrdiff_t',
}

STDLIB_FUNCTIONS: Dict[str, str] = {
    # func_name: required_header
    'printf':   'stdio.h',  'fprintf':  'stdio.h',
    'scanf':    'stdio.h',  'fscanf':   'stdio.h',
    'fopen':    'stdio.h',  'fclose':   'stdio.h',
    'fgets':    'stdio.h',  'fputs':    'stdio.h',
    'gets':     'stdio.h',  'puts':     'stdio.h',
    'sprintf':  'stdio.h',  'sscanf':   'stdio.h',
    'malloc':   'stdlib.h', 'calloc':   'stdlib.h',
    'realloc':  'stdlib.h', 'free':     'stdlib.h',
    'exit':     'stdlib.h', 'atoi':     'stdlib.h',
    'atof':     'stdlib.h', 'strtol':   'stdlib.h',
    'strlen':   'string.h', 'strcpy':   'string.h',
    'strncpy':  'string.h', 'strcat':   'string.h',
    'strncat':  'string.h', 'strcmp':   'string.h',
    'strncmp':  'string.h', 'strchr':   'string.h',
    'strstr':   'string.h', 'strtok':   'string.h',
    'memcpy':   'string.h', 'memset':   'string.h',
    'memmove':  'string.h',
    'sqrt':     'math.h',   'pow':      'math.h',
    'abs':      'math.h',   'fabs':     'math.h',
    'sin':      'math.h',   'cos':      'math.h',
    'ceil':     'math.h',   'floor':    'math.h',
    'assert':   'assert.h',
    'time':     'time.h',   'clock':    'time.h',
    'isdigit':  'ctype.h',  'isalpha':  'ctype.h',
    'toupper':  'ctype.h',  'tolower':  'ctype.h',
}


# ---------------------------------------------------------------------------
# LEXICAL checks
# ---------------------------------------------------------------------------

def _check_lex002(lines, source) -> List[Violation]:
    """LEX002: invalid escape sequences in string/char literals."""
    violations = []
    valid_escapes = set('nrtbfav0\\\'\"?xuU01234567')
    str_re = re.compile(r'"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'')
    for lineno, text in lines:
        for m in str_re.finditer(text):
            lit = m.group()
            i = 0
            while i < len(lit):
                if lit[i] == '\\' and i + 1 < len(lit):
                    esc = lit[i + 1]
                    if esc not in valid_escapes:
                        violations.append(Violation(
                            "LEX002",
                            f"Invalid escape sequence '\\{esc}' in literal",
                            lineno, Severity.WARNING, Phase.LEXICAL,
                            m.start() + i
                        ))
                    i += 2
                else:
                    i += 1
    return violations


def _check_lex003_004(lines, source) -> List[Violation]:
    """LEX003/LEX004: unclosed string or char literals."""
    violations = []
    for lineno, text in lines:
        # Skip lines that are continuations (end with \)
        stripped = text.rstrip()
        if stripped.endswith('\\'):
            continue
        # Count unescaped quotes
        in_string = False
        in_char = False
        i = 0
        while i < len(text):
            c = text[i]
            if c == '\\':
                i += 2
                continue
            if c == '"' and not in_char:
                in_string = not in_string
            elif c == "'" and not in_string:
                in_char = not in_char
            i += 1
        if in_string:
            violations.append(Violation(
                "LEX003", "Unclosed string literal", lineno, Severity.ERROR, Phase.LEXICAL
            ))
        if in_char:
            violations.append(Violation(
                "LEX004", "Unclosed character literal", lineno, Severity.ERROR, Phase.LEXICAL
            ))
    return violations


def _check_lex005(lines, source) -> List[Violation]:
    """LEX005: multi-character char literals like 'ab'."""
    violations = []
    multi_char = re.compile(r"'(?:[^'\\]|\\.)(?:[^'\\]|\\.)+?'")
    for lineno, text in lines:
        if multi_char.search(text):
            violations.append(Violation(
                "LEX005", "Multi-character character literal (implementation-defined behaviour)",
                lineno, Severity.WARNING, Phase.LEXICAL
            ))
    return violations


# ---------------------------------------------------------------------------
# SYNTAX checks
# ---------------------------------------------------------------------------

def _check_syn002(lines, source) -> List[Violation]:
    """SYN002: missing semicolon at end of statement."""
    violations = []
    # Patterns that must end with ; but commonly don't
    # Look for lines that look like statements/declarations but lack semicolon
    needs_semi = re.compile(
        r'^\s*(?:'
        r'(?:(?:int|char|float|double|long|short|unsigned|signed|void|bool|size_t)\s+)'
        r'(?:\*+\s*)?[A-Za-z_]\w*(?:\s*\[[^\]]*\])?'   # variable declaration
        r'(?:\s*=\s*[^{][^;{]*)?'                        # optional initializer
        r'|[A-Za-z_]\w*\s*\([^)]*\)'                    # function call
        r'|(?:return|break|continue)\s*[^;{]*'           # control-flow
        r')\s*$'
    )
    block_starts = re.compile(r'[{}\(\)#]|//')
    for lineno, text in lines:
        stripped = text.strip()
        if not stripped:
            continue
        if block_starts.search(stripped):
            continue
        if stripped.startswith(('//', '/*', '*', '#')):
            continue
        if stripped.endswith((';', '{', '}', ',')):
            continue
        if needs_semi.match(text):
            violations.append(Violation(
                "SYN002", "Possible missing semicolon at end of statement",
                lineno, Severity.ERROR, Phase.SYNTAX
            ))
    return violations


def _check_syn003_to_008(lines, source) -> List[Violation]:
    """SYN003-008: unmatched brackets, braces, parentheses."""
    violations = []
    clean = _strip_strings(_strip_comments(source))

    pairs = {'{': ('}', 'SYN003', 'SYN004'),
             '(': (')', 'SYN005', 'SYN006'),
             '[': (']', 'SYN007', 'SYN008')}

    for opener, (closer, open_rule, close_rule) in pairs.items():
        stack = []
        for lineno, text in _lines(clean):
            for col, ch in enumerate(text):
                if ch == opener:
                    stack.append((lineno, col))
                elif ch == closer:
                    if stack:
                        stack.pop()
                    else:
                        violations.append(Violation(
                            close_rule,
                            f"Unmatched closing '{closer}'",
                            lineno, Severity.ERROR, Phase.SYNTAX, col
                        ))
        for lineno, col in stack:
            violations.append(Violation(
                open_rule,
                f"Unmatched opening '{opener}'",
                lineno, Severity.ERROR, Phase.SYNTAX, col
            ))
    return violations


def _check_syn009(lines, source) -> List[Violation]:
    """SYN009: empty function body {}."""
    violations = []
    # function definition followed immediately by {}
    func_re = re.compile(
        r'^\s*(?:(?:static|inline|extern|const|unsigned|signed|long|short|void|int|char|float|double|'
        r'size_t|uint\w*|int\w*)[\s*]+)+[A-Za-z_]\w*\s*\([^)]*\)\s*\{\s*\}'
    )
    for lineno, text in lines:
        if func_re.match(text):
            violations.append(Violation(
                "SYN009", "Empty function body",
                lineno, Severity.WARNING, Phase.SYNTAX
            ))
    return violations


def _check_syn010(lines, source) -> List[Violation]:
    """SYN010: else without matching if."""
    violations = []
    clean = _strip_comments(source)
    # Very simplistic: count ifs vs elses in running scope
    if_count = 0
    for lineno, text in _lines(clean):
        if_count += len(re.findall(r'\bif\s*\(', text))
        else_matches = re.findall(r'\belse\b', text)
        for _ in else_matches:
            if if_count > 0:
                if_count -= 1
            else:
                violations.append(Violation(
                    "SYN010", "'else' without matching 'if'",
                    lineno, Severity.ERROR, Phase.SYNTAX
                ))
    return violations


def _check_syn011(lines, source) -> List[Violation]:
    """SYN011: unclosed block comment."""
    violations = []
    open_count = 0
    open_line = 1
    for lineno, text in lines:
        opens  = len(re.findall(r'/\*', text))
        closes = len(re.findall(r'\*/', text))
        for _ in range(opens):
            open_count += 1
            open_line = lineno
        for _ in range(closes):
            if open_count > 0:
                open_count -= 1
    if open_count > 0:
        violations.append(Violation(
            "SYN011", "Unclosed block comment /* ... */",
            open_line, Severity.ERROR, Phase.SYNTAX
        ))
    return violations


# ---------------------------------------------------------------------------
# SEMANTIC checks
# ---------------------------------------------------------------------------

def _check_sem001(lines, source) -> List[Violation]:
    """SEM001: function names must be snake_case."""
    violations = []
    pattern = re.compile(
        r'^\s*(?:(?:static|inline|extern|const|unsigned|signed|long|short|void|int|char|float|double|'
        r'size_t|uint\w*|int\w*)[\s*]+)+([A-Za-z_]\w*)\s*\(',
        re.MULTILINE
    )
    skip = {'if', 'for', 'while', 'switch', 'return', 'sizeof', 'main',
            'printf', 'scanf', 'malloc', 'calloc', 'free', 'realloc',
            'strlen', 'strcpy', 'strncpy', 'fprintf', 'fopen', 'fclose'}
    for lineno, text in lines:
        m = pattern.match(text)
        if m:
            name = m.group(1)
            if name in skip or name in C_KEYWORDS:
                continue
            if not re.match(r'^[a-z_][a-z0-9_]*$', name):
                violations.append(Violation(
                    "SEM001", f"Function '{name}' should use snake_case",
                    lineno, Severity.WARNING, Phase.SEMANTIC
                ))
    return violations


def _check_sem002(lines, source) -> List[Violation]:
    """SEM002: more than 5 parameters."""
    violations = []
    func_re = re.compile(
        r'^\s*(?:(?:static|inline|extern|const|unsigned|signed|long|short|void|int|char|float|double|'
        r'size_t|uint\w*|int\w*)[\s*]+)+[A-Za-z_]\w*\s*\(([^)]*)\)'
    )
    for lineno, text in lines:
        m = func_re.match(text)
        if not m:
            continue
        params_str = m.group(1).strip()
        if not params_str or params_str == 'void':
            continue
        params = [p for p in params_str.split(',') if p.strip()]
        if len(params) > 5:
            violations.append(Violation(
                "SEM002", f"Function has {len(params)} parameters (max recommended: 5)",
                lineno, Severity.WARNING, Phase.SEMANTIC
            ))
    return violations


def _check_sem003(lines, source) -> List[Violation]:
    """SEM003: use of gets()."""
    violations = []
    for lineno, text in lines:
        if re.search(r'\bgets\s*\(', text):
            violations.append(Violation(
                "SEM003", "gets() is unsafe (buffer overflow); use fgets() instead",
                lineno, Severity.ERROR, Phase.SEMANTIC
            ))
    return violations


def _check_sem004(lines, source) -> List[Violation]:
    """SEM004: use of strcpy."""
    violations = []
    for lineno, text in lines:
        if re.search(r'\bstrcpy\s*\(', text):
            violations.append(Violation(
                "SEM004", "strcpy() is unsafe; prefer strncpy() or strlcpy()",
                lineno, Severity.WARNING, Phase.SEMANTIC
            ))
    return violations


def _check_sem005(lines, source) -> List[Violation]:
    """SEM005: magic numbers."""
    violations = []
    skip_re = re.compile(r'^\s*#\s*define\b')
    magic_re = re.compile(r'(?<!["\w])([2-9]\d*|[1-9]\d+)(?![\w"])')
    for lineno, text in lines:
        if skip_re.match(text):
            continue
        if re.search(magic_re, text):
            violations.append(Violation(
                "SEM005", "Magic number literal; consider using a named constant (#define)",
                lineno, Severity.INFO, Phase.SEMANTIC
            ))
    return violations


def _check_sem006(lines, source) -> List[Violation]:
    """SEM006: variable declared but never used."""
    violations = []
    decl_re = re.compile(
        r'^\s*(?:int|char|float|double|long|unsigned|signed|short|size_t|bool)\s+\*?([A-Za-z_]\w*)'
        r'\s*(?:\[[^\]]*\])?\s*(?:=|;)'
    )
    skip_names = {'i', 'j', 'k', 'n', 'c', 'rc', 'ret', 'err', 'status', 'result',
                  'tmp', 'temp', 'buf', 'ch', 'len', 'count', 'size', 'idx', 'pos'}
    for lineno, text in lines:
        m = decl_re.match(text)
        if not m:
            continue
        varname = m.group(1)
        if varname in skip_names or varname in C_KEYWORDS:
            continue
        other = source.splitlines()
        other[lineno - 1] = ''
        rest = '\n'.join(other)
        if not re.search(r'\b' + re.escape(varname) + r'\b', rest):
            violations.append(Violation(
                "SEM006", f"Variable '{varname}' declared but never used",
                lineno, Severity.WARNING, Phase.SEMANTIC
            ))
    return violations


def _check_sem007(lines, source) -> List[Violation]:
    """SEM007: non-void function without return."""
    violations = []
    func_re = re.compile(
        r'^\s*(int|char|float|double|long|unsigned|short|size_t|char\s*\*|void\s*\*|bool)'
        r'\s+([A-Za-z_]\w*)\s*\([^)]*\)\s*\{'
    )
    for lineno, text in lines:
        m = func_re.match(text)
        if not m:
            continue
        return_type = m.group(1).strip()
        func_name   = m.group(2)
        if return_type == 'void':
            continue
        depth = 0
        body_lines = []
        for _, t in lines[lineno - 1:]:
            depth += t.count('{') - t.count('}')
            body_lines.append(t)
            if depth <= 0:
                break
        body = '\n'.join(body_lines)
        if not re.search(r'\breturn\b', body):
            violations.append(Violation(
                "SEM007", f"Non-void function '{func_name}' appears to have no return statement",
                lineno, Severity.WARNING, Phase.SEMANTIC
            ))
    return violations


def _check_sem008(lines, source) -> List[Violation]:
    """SEM008: empty else block."""
    violations = []
    else_re = re.compile(r'\belse\s*\{?\s*\}')
    for lineno, text in lines:
        if else_re.search(text):
            violations.append(Violation(
                "SEM008", "Empty else block",
                lineno, Severity.INFO, Phase.SEMANTIC
            ))
    return violations


def _check_sem009(lines, source) -> List[Violation]:
    """SEM009: scanf with %s and no width."""
    violations = []
    for lineno, text in lines:
        if re.search(r'\bscanf\s*\(\s*"[^"]*%s', text):
            violations.append(Violation(
                "SEM009", "scanf() with %%s and no field-width; use %%Ns (N = buffer size - 1)",
                lineno, Severity.ERROR, Phase.SEMANTIC
            ))
    return violations


def _check_sem010(lines, source) -> List[Violation]:
    """SEM010: allocation result not checked for NULL."""
    violations = []
    alloc_re = re.compile(r'([A-Za-z_]\w*)\s*=\s*(?:malloc|calloc|realloc)\s*\(')
    for lineno, text in lines:
        m = alloc_re.search(text)
        if not m:
            continue
        ptr = m.group(1)
        context = '\n'.join(t for _, t in lines[lineno - 1: lineno + 6])
        if not re.search(r'\b' + re.escape(ptr) + r'\b\s*(?:==|!=)\s*NULL', context) and \
           not re.search(r'!\s*' + re.escape(ptr) + r'\b', context):
            violations.append(Violation(
                "SEM010", f"Pointer '{ptr}' from allocation not checked for NULL",
                lineno, Severity.WARNING, Phase.SEMANTIC
            ))
    return violations


def _collect_declarations(source: str) -> Dict[str, int]:
    """
    Best-effort: return {name: first_lineno} for all variable/function declarations.
    """
    declared: Dict[str, int] = {}
    clean = _strip_comments(_strip_strings(source))

    # Function definitions / declarations
    func_re = re.compile(
        r'^\s*(?:(?:static|inline|extern|const|unsigned|signed|long|short|void|int|char|float|double|'
        r'size_t|uint\w*|int\w*|bool)[\s*]+)+([A-Za-z_]\w*)\s*\(',
        re.MULTILINE
    )
    for m in func_re.finditer(clean):
        name = m.group(1)
        if name not in C_KEYWORDS:
            lineno = clean[:m.start()].count('\n') + 1
            declared.setdefault(name, lineno)

    # Variable declarations (local + global)
    decl_re = re.compile(
        r'^\s*(?:(?:const|static|extern|volatile|register|unsigned|signed|long|short|'
        r'int|char|float|double|void|bool|size_t|uint\w*|int\w*)[\s*]+)+'
        r'(\*?\s*[A-Za-z_]\w*)'
        r'(?:\s*\[[^\]]*\])?'
        r'\s*(?:=|;|,|\))',
        re.MULTILINE
    )
    for m in decl_re.finditer(clean):
        raw = m.group(1).replace('*', '').strip()
        if raw and raw not in C_KEYWORDS:
            lineno = clean[:m.start()].count('\n') + 1
            declared.setdefault(raw, lineno)

    # Struct/enum/typedef names
    typedef_re = re.compile(r'\btypedef\b[^;]+\b([A-Za-z_]\w*)\s*;', re.DOTALL)
    for m in typedef_re.finditer(clean):
        name = m.group(1)
        lineno = clean[:m.start()].count('\n') + 1
        declared.setdefault(name, lineno)

    # #define macros
    define_re = re.compile(r'^\s*#\s*define\s+([A-Za-z_]\w*)', re.MULTILINE)
    for m in define_re.finditer(source):
        name = m.group(1)
        lineno = source[:m.start()].count('\n') + 1
        declared.setdefault(name, lineno)

    return declared


def _check_sem011(lines, source) -> List[Violation]:
    """SEM011: use of undeclared variable/identifier."""
    violations = []
    declared = _collect_declarations(source)
    clean = _strip_comments(_strip_strings(_strip_preprocessor(source)))

    # Identifiers used in expressions (exclude keywords, type names, declared names)
    use_re = re.compile(r'\b([A-Za-z_][A-Za-z0-9_]*)\s*(?![\s*]*\()')  # not a function call
    known = set(declared.keys()) | C_KEYWORDS | set(STDLIB_FUNCTIONS.keys())

    reported: Set[str] = set()
    for lineno, text in _lines(clean):
        if text.strip().startswith(('//', '*', '#')):
            continue
        for m in use_re.finditer(text):
            name = m.group(1)
            if name in known or name in reported:
                continue
            if name[0].isupper():  # likely type or macro
                continue
            # Only flag if it looks like a variable (lowercase start, used after = or in expr)
            ctx = text[max(0, m.start()-3):m.end()+1]
            if re.search(r'[=+\-*/&|^!<>,(]\s*$|^\s*[=+\-*/&|^!<>,(]', ctx):
                violations.append(Violation(
                    "SEM011", f"Identifier '{name}' used but not declared",
                    lineno, Severity.ERROR, Phase.SEMANTIC
                ))
                reported.add(name)
    return violations


def _check_sem012(lines, source) -> List[Violation]:
    """SEM012: division by zero (literal denominator 0)."""
    violations = []
    div_zero = re.compile(r'/\s*0(?!\d)')
    for lineno, text in lines:
        if div_zero.search(text) and '//' not in text[:text.index('/') + 1 if '/' in text else 0]:
            violations.append(Violation(
                "SEM012", "Division by zero (literal 0 as divisor)",
                lineno, Severity.ERROR, Phase.SEMANTIC
            ))
    return violations


def _check_sem013(lines, source) -> List[Violation]:
    """SEM013: assignment (=) inside condition that looks like comparison."""
    violations = []
    # Pattern: if/while/for (...= something...) where = is not ==
    cond_assign = re.compile(r'\b(?:if|while)\s*\([^)]*(?<!=)=(?!=)[^)]*\)')
    for lineno, text in lines:
        if cond_assign.search(text):
            violations.append(Violation(
                "SEM013", "Assignment inside condition — did you mean '==' ?",
                lineno, Severity.WARNING, Phase.SEMANTIC
            ))
    return violations


def _check_sem014(lines, source) -> List[Violation]:
    """SEM014: printf/fprintf with variable as first argument (format injection)."""
    violations = []
    fmt_inject = re.compile(r'\b(?:printf|fprintf)\s*\(\s*(?!")[A-Za-z_]')
    for lineno, text in lines:
        if fmt_inject.search(text):
            violations.append(Violation(
                "SEM014", "printf/fprintf with non-literal format string (format injection risk); use printf(\"%s\", var)",
                lineno, Severity.ERROR, Phase.SEMANTIC
            ))
    return violations


def _check_sem015(lines, source) -> List[Violation]:
    """SEM015: dead code after return/break/continue."""
    violations = []
    # Match return/break/continue that ends a statement (has semicolon or is on its own line)
    terminators = re.compile(r'\b(return|break|continue)\b[^;{]*;')
    for i, (lineno, text) in enumerate(lines):
        if not terminators.search(text):
            continue
        # Look at the next non-empty line within same block
        for j in range(i + 1, min(i + 5, len(lines))):
            next_text = lines[j][1].strip()
            if not next_text:
                continue
            if next_text.startswith(('}', '//', '/*', '#', 'case ', 'default:')):
                break
            # Looks like real code
            violations.append(Violation(
                "SEM015", "Dead code: unreachable statement after return/break/continue",
                lines[j][0], Severity.WARNING, Phase.SEMANTIC
            ))
            break
    return violations


def _check_sem016(lines, source) -> List[Violation]:
    """SEM016: array index out of bounds (literal index vs declared size)."""
    violations = []
    # Find array declarations: type name[SIZE]
    decl_re = re.compile(r'\b[A-Za-z_]\w*\s+([A-Za-z_]\w*)\s*\[(\d+)\]')
    array_sizes: Dict[str, int] = {}
    for lineno, text in lines:
        m = decl_re.search(text)
        if m:
            array_sizes[m.group(1)] = int(m.group(2))

    # Find accesses: name[LITERAL_INDEX]
    access_re = re.compile(r'\b([A-Za-z_]\w*)\s*\[(\d+)\]')
    for lineno, text in lines:
        for m in access_re.finditer(text):
            name  = m.group(1)
            index = int(m.group(2))
            if name in array_sizes and index >= array_sizes[name]:
                violations.append(Violation(
                    "SEM016",
                    f"Array '{name}[{array_sizes[name]}]' accessed at index {index} (out of bounds)",
                    lineno, Severity.ERROR, Phase.SEMANTIC
                ))
    return violations


def _check_sem017(lines, source) -> List[Violation]:
    """SEM017: infinite loop (while(1) or for(;;)) without any break inside."""
    violations = []
    infinite_re = re.compile(r'\b(?:while\s*\(\s*1\s*\)|for\s*\(\s*;\s*;\s*\))')
    for i, (lineno, text) in enumerate(lines):
        if not infinite_re.search(text):
            continue
        # Collect loop body
        depth = 0
        body_lines = []
        for _, t in lines[i:]:
            depth += t.count('{') - t.count('}')
            body_lines.append(t)
            if depth <= 0 and body_lines:
                break
        body = '\n'.join(body_lines)
        if not re.search(r'\bbreak\b', body) and not re.search(r'\breturn\b', body):
            violations.append(Violation(
                "SEM017", "Infinite loop (while(1)/for(;;)) with no break or return",
                lineno, Severity.WARNING, Phase.SEMANTIC
            ))
    return violations


def _check_sem018(lines, source) -> List[Violation]:
    """SEM018: use of deprecated/dangerous functions."""
    dangerous = {
        'sprintf':  "sprintf() can overflow; use snprintf() instead",
        'strcat':   "strcat() is unsafe; use strncat() instead",
        'strtok':   "strtok() is not re-entrant; use strtok_r() instead",
        'mktemp':   "mktemp() is insecure; use mkstemp() instead",
        'tmpnam':   "tmpnam() is insecure; use tmpfile() instead",
    }
    violations = []
    for lineno, text in lines:
        for func, msg in dangerous.items():
            if re.search(r'\b' + func + r'\s*\(', text):
                violations.append(Violation(
                    "SEM018", msg,
                    lineno, Severity.WARNING, Phase.SEMANTIC
                ))
    return violations


def _check_sem019(lines, source) -> List[Violation]:
    """SEM019: variable shadowing (inner scope re-declares outer scope variable)."""
    violations = []
    decl_re = re.compile(
        r'^\s*(?:int|char|float|double|long|unsigned|signed|short|size_t|bool)\s+\*?([A-Za-z_]\w*)'
    )
    declared_vars: List[Tuple[str, int]] = []  # (name, brace_depth)
    depth = 0
    for lineno, text in lines:
        depth += text.count('{') - text.count('}')
        m = decl_re.match(text)
        if m:
            name = m.group(1)
            # Check if already declared at a shallower depth
            for prev_name, prev_depth in declared_vars:
                if prev_name == name and prev_depth < depth:
                    violations.append(Violation(
                        "SEM019", f"Variable '{name}' shadows an outer-scope declaration",
                        lineno, Severity.WARNING, Phase.SEMANTIC
                    ))
                    break
            declared_vars.append((name, depth))
    return violations


def _check_sem020(lines, source) -> List[Violation]:
    """SEM020: using a stdlib function without including its header."""
    violations = []
    # Collect included headers
    included = set()
    for _, text in lines:
        m = re.match(r'^\s*#\s*include\s*[<"]([^>"]+)[>"]', text)
        if m:
            included.add(m.group(1))

    reported: Set[str] = set()
    for lineno, text in lines:
        for func, header in STDLIB_FUNCTIONS.items():
            if func in reported:
                continue
            if re.search(r'\b' + re.escape(func) + r'\s*\(', text):
                if header not in included:
                    violations.append(Violation(
                        "SEM020",
                        f"Function '{func}' used but <{header}> not included",
                        lineno, Severity.WARNING, Phase.SEMANTIC
                    ))
                    reported.add(func)
    return violations


def _check_sem021(lines, source) -> List[Violation]:
    """SEM021: signed/unsigned comparison."""
    violations = []
    # Look for patterns like: int_var < unsigned_var or > size_t etc.
    su_cmp = re.compile(r'\b(?:unsigned|size_t|uint\w+)\b[^;=\n]*(?:<|>|<=|>=)[^;=\n]*\b(?:int|signed)\b')
    su_cmp2 = re.compile(r'\b(?:int|signed)\b[^;=\n]*(?:<|>|<=|>=)[^;=\n]*\b(?:unsigned|size_t|uint\w+)\b')
    for lineno, text in lines:
        if su_cmp.search(text) or su_cmp2.search(text):
            violations.append(Violation(
                "SEM021", "Signed/unsigned comparison — may produce unexpected results",
                lineno, Severity.WARNING, Phase.SEMANTIC
            ))
    return violations


def _check_sem022(lines, source) -> List[Violation]:
    """SEM022: implicit function declaration (called before declared)."""
    violations = []
    declared_funcs: Set[str] = set()
    # First pass: collect all function declarations and definitions
    func_decl_re = re.compile(
        r'^\s*(?:(?:static|inline|extern|const|unsigned|signed|long|short|void|int|char|float|double|'
        r'size_t|uint\w*|int\w*|bool)[\s*]+)+([A-Za-z_]\w*)\s*\('
    )
    for _, text in lines:
        m = func_decl_re.match(text)
        if m:
            name = m.group(1)
            if name not in C_KEYWORDS:
                declared_funcs.add(name)
    declared_funcs |= set(STDLIB_FUNCTIONS.keys())

    # Second pass: find calls to undeclared functions
    call_re = re.compile(r'\b([A-Za-z_]\w*)\s*\(')
    reported: Set[str] = set()
    for lineno, text in lines:
        if func_decl_re.match(text):
            continue  # skip definition lines
        for m in call_re.finditer(text):
            name = m.group(1)
            if name in declared_funcs or name in C_KEYWORDS or name in reported:
                continue
            if name[0].isupper():
                continue  # likely macro
            violations.append(Violation(
                "SEM022", f"Function '{name}' called but not declared before use",
                lineno, Severity.WARNING, Phase.SEMANTIC
            ))
            reported.add(name)
    return violations


def _check_sem023(lines, source) -> List[Violation]:
    """SEM023: pointer arithmetic on void*."""
    violations = []
    for lineno, text in lines:
        if re.search(r'\bvoid\s*\*[^;)]*[+\-]', text):
            violations.append(Violation(
                "SEM023", "Pointer arithmetic on void* is undefined behaviour; cast to char* first",
                lineno, Severity.WARNING, Phase.SEMANTIC
            ))
    return violations


def _check_sem024(lines, source) -> List[Violation]:
    """SEM024: potential double-free pattern."""
    violations = []
    free_re = re.compile(r'\bfree\s*\(\s*([A-Za-z_]\w*)\s*\)')
    freed: Dict[str, int] = {}
    for lineno, text in lines:
        for m in free_re.finditer(text):
            ptr = m.group(1)
            if ptr in freed:
                violations.append(Violation(
                    "SEM024", f"Possible double-free of '{ptr}' (already freed at line {freed[ptr]})",
                    lineno, Severity.ERROR, Phase.SEMANTIC
                ))
            else:
                freed[ptr] = lineno
    return violations


def _check_sem025(lines, source) -> List[Violation]:
    """SEM025: global variable mutated inside function."""
    violations = []
    # Find global variable names (declared outside any braces)
    global_vars: Set[str] = set()
    depth = 0
    decl_re = re.compile(
        r'^\s*(?:int|char|float|double|long|unsigned|signed|short|size_t|bool)\s+\*?([A-Za-z_]\w*)'
    )
    for _, text in lines:
        if depth == 0:
            m = decl_re.match(text)
            if m:
                global_vars.add(m.group(1))
        depth += text.count('{') - text.count('}')
        if depth < 0:
            depth = 0

    if not global_vars:
        return violations

    # Find assignments to global vars inside functions
    assign_re = re.compile(r'\b([A-Za-z_]\w*)\s*(?:\[.*?\])?\s*(?:=|\+=|-=|\*=|/=)')
    depth = 0
    for lineno, text in lines:
        depth += text.count('{') - text.count('}')
        if depth > 0:
            for m in assign_re.finditer(text):
                name = m.group(1)
                if name in global_vars:
                    violations.append(Violation(
                        "SEM025", f"Global variable '{name}' mutated inside function (side-effect)",
                        lineno, Severity.INFO, Phase.SEMANTIC
                    ))
    return violations


# ---------------------------------------------------------------------------
# CODEGEN checks
# ---------------------------------------------------------------------------

def _check_cgn001(lines, source) -> List[Violation]:
    """CGN001: non-void function with no guaranteed return path."""
    # More thorough version of SEM007 — checks ALL branches
    violations = []
    func_re = re.compile(
        r'^\s*(int|char|float|double|long|unsigned|short|size_t|bool)\s+([A-Za-z_]\w*)\s*\([^)]*\)\s*\{'
    )
    for lineno, text in lines:
        m = func_re.match(text)
        if not m:
            continue
        func_name = m.group(2)
        depth = 0
        body_lines = []
        for _, t in lines[lineno - 1:]:
            depth += t.count('{') - t.count('}')
            body_lines.append(t)
            if depth <= 0:
                break
        body = '\n'.join(body_lines)
        returns = re.findall(r'\breturn\s+\S', body)
        # If there's an if/else but only one branch has return, flag it
        has_if = bool(re.search(r'\bif\s*\(', body))
        has_else = bool(re.search(r'\belse\b', body))
        if has_if and not has_else and len(returns) == 1:
            violations.append(Violation(
                "CGN001",
                f"Function '{func_name}' may not return a value on all code paths",
                lineno, Severity.WARNING, Phase.CODEGEN
            ))
    return violations


def _check_cgn002(lines, source) -> List[Violation]:
    """CGN002: function return value ignored for error-prone functions."""
    violations = []
    critical = {'fopen', 'fclose', 'fread', 'fwrite', 'scanf', 'fscanf',
                'malloc', 'calloc', 'realloc', 'system', 'rename', 'remove'}
    for lineno, text in lines:
        stripped = text.strip()
        for func in critical:
            if not re.search(r'\b' + re.escape(func) + r'\s*\(', stripped):
                continue
            # Flag if the line doesn't contain an assignment
            before_call = stripped.split(func)[0]
            if '=' not in before_call and not stripped.startswith('if') and not stripped.startswith('while'):
                violations.append(Violation(
                    "CGN002",
                    f"Return value of '{func}()' is ignored — check for errors",
                    lineno, Severity.WARNING, Phase.CODEGEN
                ))
    return violations


def _check_cgn003(lines, source) -> List[Violation]:
    """CGN003: pointer parameter that is never written to should be const."""
    violations = []
    # Find function definitions with pointer params
    func_re = re.compile(
        r'^\s*(?:(?:static|inline|extern|void|int|char|float|double|long|short|unsigned|signed|'
        r'size_t|bool)[\s*]+)+[A-Za-z_]\w*\s*\(([^)]+)\)'
    )
    for lineno, text in lines:
        m = func_re.match(text)
        if not m:
            continue
        params_str = m.group(1)
        # Find pointer params without const
        ptr_params = re.findall(r'\b(?!const\b)(?:int|char|float|double|void)\s*\*\s*([A-Za-z_]\w*)', params_str)
        for param in ptr_params:
            # Check if the param is written to in the next ~30 lines
            context_lines = lines[lineno - 1: lineno + 30]
            body = '\n'.join(t for _, t in context_lines)
            if not re.search(r'\b' + re.escape(param) + r'\s*(?:\[.*?\]\s*)?=(?!=)', body):
                violations.append(Violation(
                    "CGN003",
                    f"Parameter '{param}' is a pointer that is never written to; consider 'const'",
                    lineno, Severity.INFO, Phase.CODEGEN
                ))
    return violations


# ---------------------------------------------------------------------------
# public entry point
# ---------------------------------------------------------------------------

CHECKS = [
    _check_lex002, _check_lex003_004, _check_lex005,
    _check_syn002, _check_syn003_to_008, _check_syn009,
    _check_syn010, _check_syn011,
    _check_sem001, _check_sem002, _check_sem003, _check_sem004,
    _check_sem005, _check_sem006, _check_sem007, _check_sem008,
    _check_sem009, _check_sem010, _check_sem011, _check_sem012,
    _check_sem013, _check_sem014, _check_sem015, _check_sem016,
    _check_sem017, _check_sem018, _check_sem019, _check_sem020,
    _check_sem021, _check_sem022, _check_sem023, _check_sem024,
    _check_sem025,
    _check_cgn001, _check_cgn002, _check_cgn003,
]


class CAnalyzer:
    """Run all C rules against source text and collect Violations."""

    def __init__(self):
        self.violations: List[Violation] = []

    def analyze(self, source: str) -> List[Violation]:
        clean = _strip_comments(source)
        numbered = _lines(clean)
        for check in CHECKS:
            try:
                self.violations.extend(check(numbered, clean))
            except Exception:
                pass  # never crash the whole analyzer on one rule
        # Deduplicate by (line, rule)
        seen = set()
        unique = []
        for v in sorted(self.violations, key=lambda x: x.line):
            key = (v.line, v.rule)
            if key not in seen:
                seen.add(key)
                unique.append(v)
        return unique
