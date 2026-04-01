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

---

## Java Rules

| ID    | Severity | Description                                        |
|-------|----------|----------------------------------------------------|
| JV001 | ERROR    | Class name not in `PascalCase`                     |
| JV002 | WARNING  | Method name not in `camelCase`                     |
| JV003 | ERROR    | Empty catch block                                  |
| JV004 | WARNING  | Magic number — bare integer literal in expression  |
| JV005 | INFO     | `System.out.println` left in code                  |

### JV001 — PascalCase class names

Bad:
```java
public class myClass { }
public class my_class { }
```
Good:
```java
public class MyClass { }
```

### JV003 — empty catch block

Bad:
```java
catch (Exception e) { }
```
Good:
```java
catch (Exception e) {
    logger.error("Failed: " + e.getMessage());
}
```
