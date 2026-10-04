from .ast import (
    Assignment, BinaryExpression, ComparisonExpression, Identifier,
    IfStatement, NumberLiteral, OutputStatement, Program,
    StringLiteral, VariableDeclaration,
)
from .errors import HLError
from .lexer import Token


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.position = 0

    @property
    def current(self) -> Token:
        return self.tokens[self.position]

    def take(self) -> Token:
        token = self.current
        self.position += 1
        return token

    def expect(self, kind: str, message: str) -> Token:
        if self.current.kind != kind:
            raise HLError(message, self.current.line, self.current.column)
        return self.take()

    def parse(self) -> Program:
        first = self.current
        statements = []
        while self.current.kind != "EOF":
            statements.append(self.statement())
        return Program(first, statements)

    def statement(self):
        token = self.current
        if token.kind == "IDENTIFIER":
            self.take()
            if self.current.kind == "COLON":
                self.take()
                if self.current.kind not in ("INTEGER", "DOUBLE"):
                    raise HLError("expected type 'integer' or 'double'", self.current.line, self.current.column)
                type_token = self.take()
                self.expect("SEMICOLON", "expected ';' after declaration")
                return VariableDeclaration(token, token.value, type_token.value)
            self.expect("ASSIGN", "expected ':' for declaration or ':='/'=' for assignment")
            expression = self.expression()
            self.expect("SEMICOLON", "expected ';' after assignment")
            return Assignment(token, token.value, expression)
        if token.kind == "OUTPUT":
            self.take()
            self.expect("OUTPUT_OPERATOR", "expected '<<' after output")
            if self.current.kind == "STRING_LITERAL":
                string = self.take()
                expression = StringLiteral(string, string.value)
            else:
                expression = self.expression()
            self.expect("SEMICOLON", "expected ';' after output")
            return OutputStatement(token, expression)
        if token.kind == "IF":
            self.take()
            self.expect("LPAREN", "expected '(' after if")
            left = self.expression()
            if self.current.kind not in ("LESS", "GREATER", "EQUAL", "NOT_EQUAL"):
                raise HLError("expected comparison '<', '>', '==' or '!='", self.current.line, self.current.column)
            operator = self.take()
            right = self.expression()
            self.expect("RPAREN", "expected ')' after if condition")
            condition = ComparisonExpression(operator, left, operator.lexeme, right)
            return IfStatement(token, condition, self.statement())
        raise HLError("expected declaration, assignment, output or if statement", token.line, token.column)

    def expression(self):
        # Build a left-associative tree: 8-3-2 means (8-3)-2.
        left = self.primary()
        while self.current.kind in ("PLUS", "MINUS"):
            operator = self.take()
            left = BinaryExpression(operator, left, operator.lexeme, self.primary())
        return left

    def primary(self):
        token = self.current
        if token.kind in ("INTEGER_LITERAL", "DOUBLE_LITERAL"):
            self.take()
            return NumberLiteral(token, token.value)
        if token.kind == "IDENTIFIER":
            self.take()
            return Identifier(token, token.value)
        raise HLError("expected a number or identifier", token.line, token.column)
