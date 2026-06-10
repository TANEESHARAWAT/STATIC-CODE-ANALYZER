"""
bad_code.py — Sample Python file with intentional violations.
Run: python main.py samples/bad_code.py
"""

# PY001: not snake_case
def MyBadFunction(a, b, c, d, e, f):   # PY002: 6 params, PY013: no docstring
    l = a + b                           # PY004: ambiguous name 'l'
    unused_var = 123                    # PY005: never used
    try:
        result = l / c
    except:                             # PY003: bare except
        pass                            # PY011: empty except block
    return result


# PY007: mutable default argument
def append_item(item, container=[]):
    container.append(item)
    return container


# PY008: comparison with None using ==
def check_none(x):
    if x == None:                       # PY008
        return True
    return False


# PY009: comparison with True using ==
def check_flag(flag):
    if flag == True:                    # PY009
        print("yes")


# PY013: missing docstring on public function
def calculate(x, y):
    result = x * 42 + 100              # PY014: magic numbers
    return result


# PY015: global variable usage
counter = 0

def increment():
    global counter                      # PY015
    counter += 1


# PY012: deeply nested code
def deeply_nested(a, b, c, d):
    if a:
        if b:
            if c:
                if d:
                    for i in range(10):
                        while True:
                            pass        # PY012: too deep


# Clean function — zero violations expected
def good_function(x, y):
    """Divides x by y safely."""
    if y is None:
        return 0
    try:
        return x / y
    except ZeroDivisionError:
        return 0
