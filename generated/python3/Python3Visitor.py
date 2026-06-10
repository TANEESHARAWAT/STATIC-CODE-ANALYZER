# Alias file — the analyzer imports Python3Visitor but ANTLR generates Python3ParserVisitor
from generated.python3.Python3ParserVisitor import Python3ParserVisitor as Python3Visitor

__all__ = ["Python3Visitor"]
