# Sample Python file with intentional rule violations for testing

def MyFunction(a, b, c, d, e, f):   # PY001: not snake_case | PY002: 6 params
    l = a + b                        # PY004: ambiguous variable name
    try:
        result = l / c
    except:                          # PY003: bare except
        pass
    return result


def good_function(x, y):
    """This function should produce zero violations."""
    try:
        return x / y
    except ZeroDivisionError:
        return 0
