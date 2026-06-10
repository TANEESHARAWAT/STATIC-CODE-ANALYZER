from antlr4 import Parser


class Python3ParserBase(Parser):

    def __init__(self, input, output=None):
        super().__init__(input, output)

    def isEqualToCurrentTokenText(self, t):
        return self.getCurrentToken().text == t

    def isnotEqualToCurrentTokenText(self, t):
        return not self.isEqualToCurrentTokenText(t)

    def CannotBePlusMinus(self):
        return True

    def CannotBeDotLpEq(self):
        return True
        