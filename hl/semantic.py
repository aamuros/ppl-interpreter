from dataclasses import dataclass
from decimal import Decimal

from .ast import (
    Assignment, BinaryExpression, Identifier, IfStatement, NumberLiteral,
    OutputStatement, Program, StringLiteral, VariableDeclaration,
)
from .errors import HLError


@dataclass
class Symbol:
    type_name: str
    value: int | Decimal


class SemanticChecker:
    def __init__(self):
        self.symbols: dict[str, Symbol] = {}

    def fail(self, node, message: str):
        raise HLError(message, node.token.line, node.token.column)

    def lookup(self, name: str, node) -> Symbol:
        if name not in self.symbols:
            self.fail(node, f"undeclared variable '{name}'")
        return self.symbols[name]

    def check(self, program: Program) -> dict[str, Symbol]:
        for statement in program.statements:
            self.statement(statement)
        return self.symbols

    def statement(self, node):
        if isinstance(node, VariableDeclaration):
            if node.name in self.symbols:
                self.fail(node, f"redeclaration of '{node.name}'")
            initial = 0 if node.type_name == "integer" else Decimal("0")
            self.symbols[node.name] = Symbol(node.type_name, initial)
        elif isinstance(node, Assignment):
            target = self.lookup(node.name, node)
            expression_type = self.expression_type(node.expression)
            if target.type_name == "integer" and expression_type != "integer":
                self.fail(node, f"cannot assign {expression_type} expression to integer '{node.name}'")
        elif isinstance(node, OutputStatement):
            self.expression_type(node.expression)
        elif isinstance(node, IfStatement):
            self.expression_type(node.condition.left)
            self.expression_type(node.condition.right)
            # Check even a false branch before any execution can produce output.
            self.statement(node.body)

    def expression_type(self, node) -> str:
        if isinstance(node, NumberLiteral):
            return "double" if isinstance(node.value, Decimal) else "integer"
        if isinstance(node, StringLiteral):
            return "string"
        if isinstance(node, Identifier):
            return self.lookup(node.name, node).type_name
        if isinstance(node, BinaryExpression):
            left = self.expression_type(node.left)
            right = self.expression_type(node.right)
            return "double" if "double" in (left, right) else "integer"
        raise TypeError(f"unknown expression node: {type(node).__name__}")
