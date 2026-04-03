# Analysis Rules Reference

## Python Rules

| ID    | Severity | Description                                        |
|-------|----------|----------------------------------------------------|
| PY001 | WARNING  | Function name not in `snake_case`                  |
| PY002 | WARNING  | Function has more than 5 parameters                |
| PY003 | ERROR    | Bare `except:` — no exception type specified       |
| PY004 | WARNING  | Ambiguous variable name (`l`, `O`, or `I`)         |

### PY001 — snake_case naming

Bad:
```python
def MyFunction(): ...
def calculateTotalPrice(): ...
```
Good:
```python
def my_function(): ...
def calculate_total_price(): ...
```

### PY002 — too many parameters

Bad:
```python
def process(a, b, c, d, e, f): ...
```
Good:
```python
def process(config): ...
```

### PY003 — bare except

Bad:
```python
try:
    risky_call()
except:
    pass
```
Good:
```python
try:
    risky_call()
except ValueError as e:
    handle(e)
```

### PY004 — ambiguous variable names

Bad:
```python
l = 1
O = 0
I = 1
```
Good:
```python
count = 1
zero = 0
index = 1
```
