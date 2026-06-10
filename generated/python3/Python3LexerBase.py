from antlr4 import Lexer
from antlr4.Token import CommonToken
from collections import deque
import sys


class Python3LexerBase(Lexer):

    def __init__(self, input, output=sys.stdout):
        super().__init__(input, output)
        self._tokens = deque()
        self._indents = []
        self._opened = 0

    def reset(self):
        self._tokens = deque()
        self._indents = []
        self._opened = 0
        super().reset()

    def emitToken(self, token):
        super().emitToken(token)
        self._tokens.append(token)

    def nextToken(self):
        if self._input.LA(1) == -1 and self._indents:
            self._tokens.append(self._make(self.NEWLINE, "\n"))
            while self._indents:
                self._tokens.append(self._make(self.DEDENT, ""))
                self._indents.pop()

        tok = super().nextToken()

        if self._tokens:
            return self._tokens.popleft()

        return tok

    def _make(self, ttype, text):
        i = max(0, self.getCharIndex() - 1)
        t = CommonToken(
            source=(self, self._input),
            type=ttype,
            channel=self.DEFAULT_TOKEN_CHANNEL,
            start=i,
            stop=i
        )
        t.text = text
        return t

    @staticmethod
    def getIndentationCount(spaces):
        count = 0
        for c in spaces:
            if c == "\t":
                count += 8 - (count % 8)
            else:
                count += 1
        return count

    def atStartOfInput(self):
        return self.getCharIndex() == 0

    def openBrace(self):
        self._opened += 1

    def closeBrace(self):
        self._opened -= 1

    def onNewLine(self):
        new_line = self.text.replace("\r\n", "\n").replace("\r", "\n")

        la = self._input.LA(1)
        next_char = chr(la) if 0 <= la <= 0x10FFFF else ""

        if self._opened > 0 or next_char in ("\n", "\r", "\f", "#"):
            self.skip()
            return

        self._tokens.append(self._make(self.NEWLINE, new_line))

        spaces = ""
        i = 1
        while True:
            la = self._input.LA(i)
            if la == -1:
                break
            c = chr(la) if 0 <= la <= 0x10FFFF else ""
            if c in (" ", "\t"):
                spaces += c
                i += 1
            else:
                break

        indent = self.getIndentationCount(spaces)
        previous = self._indents[-1] if self._indents else 0

        if indent == previous:
            self.skip()
        elif indent > previous:
            self._indents.append(indent)
            self._tokens.append(self._make(self.INDENT, spaces))
        else:
            while self._indents and self._indents[-1] > indent:
                self._tokens.append(self._make(self.DEDENT, ""))
                self._indents.pop()

    def reportAmbiguity(self, *args):
        pass

    def reportAttemptingFullContext(self, *args):
        pass

    def reportContextSensitivity(self, *args):
        pass