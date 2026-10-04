from decimal import Decimal, ROUND_HALF_UP, localcontext
from typing import Callable

from .ast import (
    Assignment, BinaryExpression, ComparisonExpression, Identifier,
    IfStatement, NumberLiteral, OutputStatement, Program, StringLiteral,
    VariableDeclaration,
)
from .semantic import Symbol


def decimal_precision(*values: Decimal) -> int:
    """Allow exact decimal addition/subtraction even for long literals."""
    places = max(0, *(-value.as_tuple().exponent for value in values))
    whole_digits = max(1, *(value.adjusted() + 1 for value in values))
    return whole_digits + places + 2


def format_value(value: int | Decimal | str) -> str:
    if isinstance(value, Decimal):
        with localcontext() as context:
            context.prec = decimal_precision(value)
            rounded = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if rounded == 0:
            return "0"  # Avoid displaying a rounded negative zero.
        return format(rounded, "f").rstrip("0").rstrip(".")
    return str(value)


class Evaluator:
    def __init__(self, symbols: dict[str, Symbol], emit: Callable[[str], None] = print):
        self.symbols = symbols
        self.emit = emit

    def execute(self, program: Program):
        for statement in program.statements:
            self.statement(statement)

    def statement(self, node):
        if isinstance(node, VariableDeclaration):
            # Declarations were entered in the global table during validation.
            return
        if isinstance(node, Assignment):
            symbol = self.symbols[node.name]
            value = self.expression(node.expression)
            symbol.value = Decimal(value) if symbol.type_name == "double" else value
        elif isinstance(node, OutputStatement):
            self.emit(format_value(self.expression(node.expression)))
        elif isinstance(node, IfStatement):
            if self.expression(node.condition):
                self.statement(node.body)

    def expression(self, node):
        if isinstance(node, (NumberLiteral, StringLiteral)):
            return node.value
        if isinstance(node, Identifier):
            return self.symbols[node.name].value
        if isinstance(node, BinaryExpression):
            left, right = self.expression(node.left), self.expression(node.right)
            if isinstance(left, Decimal) or isinstance(right, Decimal):
                left, right = Decimal(left), Decimal(right)
                with localcontext() as context:
                    context.prec = decimal_precision(left, right)
                    return left + right if node.operator == "+" else left - right
            return left + right if node.operator == "+" else left - right
        if isinstance(node, ComparisonExpression):
            left, right = self.expression(node.left), self.expression(node.right)
            if node.operator == "<":
                return left < right
            if node.operator == ">":
                return left > right
            if node.operator == "==":
                return left == right
            return left != right
        raise TypeError(f"unknown expression node: {type(node).__name__}")
