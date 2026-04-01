# Grammars

Place ANTLR4 grammar files here before running code generation.

Download from: https://github.com/antlr/grammars-v4

Files needed:
- `Python3.g4`  →  grammars-v4/python/python3/Python3.g4
- `Java8.g4`    →  grammars-v4/java/java8/Java8.g4

Then run from the project root:
```bash
antlr4 -Dlanguage=Python3 -visitor -o generated/python3 grammars/Python3.g4
antlr4 -Dlanguage=Python3 -visitor -o generated/java8  grammars/Java8.g4
```
