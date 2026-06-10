"""
Tests for the C static analyzer rules.
Run with: python -m pytest tests/ -v
   or:    python -m unittest discover tests/
"""

import unittest
import tempfile
import os
from analyzers.c_analyzer import CAnalyzer


def analyze(code: str):
    return CAnalyzer().analyze(code)


def rule_ids(violations):
    return {v.rule for v in violations}


class TestLexicalRules(unittest.TestCase):

    def test_lex002_invalid_escape(self):
        code = 'void f() { char *s = "hello \\q world"; }'
        ids = rule_ids(analyze(code))
        self.assertIn("LEX002", ids)

    def test_lex003_unclosed_string(self):
        code = 'void f() { char *s = "unclosed; }'
        ids = rule_ids(analyze(code))
        self.assertIn("LEX003", ids)

    def test_lex005_multichar(self):
        code = "void f() { char c = 'ab'; }"
        ids = rule_ids(analyze(code))
        self.assertIn("LEX005", ids)


class TestSyntaxRules(unittest.TestCase):

    def test_syn003_unmatched_open_brace(self):
        code = "void f() { int x = 1;\n"
        ids = rule_ids(analyze(code))
        self.assertIn("SYN003", ids)

    def test_syn006_unmatched_close_paren(self):
        code = "void f() { int x = (1 + 2)); }"
        ids = rule_ids(analyze(code))
        self.assertIn("SYN006", ids)

    def test_syn011_unclosed_block_comment(self):
        code = "/* this comment never closes\nvoid f() {}"
        ids = rule_ids(analyze(code))
        self.assertIn("SYN011", ids)


class TestSemanticRules(unittest.TestCase):

    def test_sem001_camel_case(self):
        code = "int BadName(int x) { return x; }"
        ids = rule_ids(analyze(code))
        self.assertIn("SEM001", ids)

    def test_sem001_snake_case_ok(self):
        code = "int good_name(int x) { return x; }"
        ids = rule_ids(analyze(code))
        self.assertNotIn("SEM001", ids)

    def test_sem002_too_many_params(self):
        code = "int f(int a, int b, int c, int d, int e, int g) { return 0; }"
        ids = rule_ids(analyze(code))
        self.assertIn("SEM002", ids)

    def test_sem003_gets(self):
        code = '#include <stdio.h>\nvoid f() { char b[64]; gets(b); }'
        ids = rule_ids(analyze(code))
        self.assertIn("SEM003", ids)

    def test_sem004_strcpy(self):
        code = '#include <string.h>\nvoid f(char *s) { char d[64]; strcpy(d, s); }'
        ids = rule_ids(analyze(code))
        self.assertIn("SEM004", ids)

    def test_sem009_scanf_no_width(self):
        code = '#include <stdio.h>\nvoid f() { char n[32]; scanf("%s", n); }'
        ids = rule_ids(analyze(code))
        self.assertIn("SEM009", ids)

    def test_sem010_malloc_no_null_check(self):
        code = '#include <stdlib.h>\nvoid f() { int *p = malloc(100); p[0] = 1; free(p); }'
        ids = rule_ids(analyze(code))
        self.assertIn("SEM010", ids)

    def test_sem012_division_by_zero(self):
        code = 'void f() { int x = 10 / 0; }'
        ids = rule_ids(analyze(code))
        self.assertIn("SEM012", ids)

    def test_sem013_assign_in_condition(self):
        code = 'void f(int x) { if (x = 5) { } }'
        ids = rule_ids(analyze(code))
        self.assertIn("SEM013", ids)

    def test_sem014_format_injection(self):
        code = '#include <stdio.h>\nvoid f(char *s) { printf(s); }'
        ids = rule_ids(analyze(code))
        self.assertIn("SEM014", ids)

    def test_sem015_dead_code(self):
        code = 'int f(int x) {\n    return x;\n    printf("dead\\n");\n}'
        ids = rule_ids(analyze(code))
        self.assertIn("SEM015", ids)

    def test_sem016_array_oob(self):
        code = 'void f() { int arr[5]; arr[5] = 1; }'
        ids = rule_ids(analyze(code))
        self.assertIn("SEM016", ids)

    def test_sem017_infinite_loop(self):
        code = 'void f() { while(1) { printf("x\\n"); } }'
        ids = rule_ids(analyze(code))
        self.assertIn("SEM017", ids)

    def test_sem018_sprintf(self):
        code = '#include <stdio.h>\nvoid f(char *s) { char b[100]; sprintf(b, s); }'
        ids = rule_ids(analyze(code))
        self.assertIn("SEM018", ids)

    def test_sem020_missing_include(self):
        code = 'void f() { char *s = malloc(10); }'
        ids = rule_ids(analyze(code))
        self.assertIn("SEM020", ids)

    def test_sem024_double_free(self):
        code = '#include <stdlib.h>\nvoid f() { int *p = malloc(4); free(p); free(p); }'
        ids = rule_ids(analyze(code))
        self.assertIn("SEM024", ids)


class TestCodeGenRules(unittest.TestCase):

    def test_cgn001_partial_return(self):
        code = 'int f(int x) { if (x > 0) { return x; } }'
        ids = rule_ids(analyze(code))
        self.assertIn("CGN001", ids)

    def test_cgn002_ignored_return(self):
        code = '#include <stdio.h>\nvoid f() { fopen("x.txt", "r"); }'
        ids = rule_ids(analyze(code))
        self.assertIn("CGN002", ids)


if __name__ == "__main__":
    unittest.main()
