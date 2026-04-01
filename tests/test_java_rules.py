"""
Unit tests for Java analysis rules.
Fill in each test after the ANTLR parser has been generated.
"""

import unittest, sys, os, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def _run(code: str):
    """Helper: write code to a temp file and run the Java analyzer on it."""
    from core.runner import analyze_java
    with tempfile.NamedTemporaryFile(suffix=".java", mode="w", delete=False) as f:
        f.write(code)
        path = f.name
    violations = analyze_java(path)
    os.unlink(path)
    return violations


class TestJavaRules(unittest.TestCase):

    def test_jv001_pascal_case(self):
        """Non-PascalCase class name triggers JV001."""
        violations = _run("public class badClass {}\n")
        rules = [v.rule for v in violations]
        self.assertIn("JV001", rules)

    def test_jv001_pascal_case_clean(self):
        """PascalCase class name does NOT trigger JV001."""
        violations = _run("public class GoodClass {}\n")
        rules = [v.rule for v in violations]
        self.assertNotIn("JV001", rules)

    def test_jv005_println(self):
        """System.out.println triggers JV005."""
        code = 'public class A { void m() { System.out.println("x"); } }\n'
        violations = _run(code)
        rules = [v.rule for v in violations]
        self.assertIn("JV005", rules)


if __name__ == "__main__":
    unittest.main()
