"""
Unit tests for Python analysis rules.
Fill in each test after the ANTLR parser has been generated.
"""

import unittest, sys, os, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def _run(code: str):
    """Helper: write code to a temp file and run the Python analyzer on it."""
    from core.runner import analyze_python
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write(code)
        path = f.name
    violations = analyze_python(path)
    os.unlink(path)
    return violations


class TestPythonRules(unittest.TestCase):

    def test_py001_snake_case(self):
        """PascalCase function name triggers PY001."""
        violations = _run("def MyFunc(): pass\n")
        rules = [v.rule for v in violations]
        self.assertIn("PY001", rules)

    def test_py001_snake_case_clean(self):
        """snake_case function name does NOT trigger PY001."""
        violations = _run("def my_func(): pass\n")
        rules = [v.rule for v in violations]
        self.assertNotIn("PY001", rules)

    def test_py002_too_many_params(self):
        """Six parameters triggers PY002."""
        violations = _run("def f(a, b, c, d, e, ff): pass\n")
        rules = [v.rule for v in violations]
        self.assertIn("PY002", rules)

    def test_py003_bare_except(self):
        """Bare except triggers PY003."""
        code = "try:\n    pass\nexcept:\n    pass\n"
        violations = _run(code)
        rules = [v.rule for v in violations]
        self.assertIn("PY003", rules)

    def test_py003_typed_except_clean(self):
        """Typed except does NOT trigger PY003."""
        code = "try:\n    pass\nexcept ValueError:\n    pass\n"
        violations = _run(code)
        rules = [v.rule for v in violations]
        self.assertNotIn("PY003", rules)


if __name__ == "__main__":
    unittest.main()
