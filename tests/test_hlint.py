import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from hl.ast import BinaryExpression, Program
from hl.errors import HLError
from hl.evaluator import Evaluator
from hl.lexer import Lexer
from hl.parser import Parser
from hl.preprocess import remove_spaces
from hl.semantic import SemanticChecker
from HLInt import run_file


ROOT = Path(__file__).resolve().parents[1]


def execute(source):
    program = Parser(Lexer(source).tokenize()).parse()
    symbols = SemanticChecker().check(program)
    output = []
    Evaluator(symbols, output.append).execute(program)
    return output, symbols


class LanguageTests(unittest.TestCase):
    def assert_output(self, source, expected):
        self.assertEqual(execute(source)[0], expected)

    def test_supplied_programs(self):
        for filename, expected in (("PROG1.HL", ["5"]), ("PROG2.HL", ["4.25"]), ("PROG3.HL", ["3"])):
            with self.subTest(filename=filename):
                self.assert_output((ROOT / filename).read_text(), expected)

    def test_declarations_and_zero_initialization(self):
        output, symbols = execute("x:integer; y:double; output<<x; output<<y;")
        self.assertEqual(output, ["0", "0"])
        self.assertEqual(symbols["x"].type_name, "integer")
        self.assertEqual(symbols["y"].type_name, "double")
        self.assertIsInstance(symbols["y"].value, Decimal)

    def test_both_assignment_spellings(self):
        self.assert_output("x:integer; x:=5; output<<x; x=3+2; output<<x;", ["5", "5"])

    def test_integer_addition(self):
        self.assert_output("output<<3+2+7;", ["12"])

    def test_integer_subtraction_and_left_associativity(self):
        self.assert_output("output<<8-3-2; output<<2-5;", ["3", "-3"])

    def test_mixed_arithmetic(self):
        self.assert_output("output<<4+2.56; output<<5-1.25;", ["6.56", "3.75"])

    def test_double_arithmetic(self):
        self.assert_output("output<<0.1+0.2; output<<4.56-1.23;", ["0.3", "3.33"])

    def test_two_decimal_output_and_negative_zero(self):
        self.assert_output("output<<1.235; output<<2.00; output<<0-1.235; output<<0-0.001;", ["1.24", "2", "-1.24", "0"])

    def test_rounding_only_at_output(self):
        self.assert_output("y:double; y:=0.004; output<<y+y; if(y>0) output<<y;", ["0.01", "0"])

    def test_long_decimal_arithmetic(self):
        self.assert_output("output<<123456789012345678901234567890.12+0.01;", ["123456789012345678901234567890.13"])

    def test_integer_to_double_assignment(self):
        output, symbols = execute("y:double; y=3+2; output<<y;")
        self.assertEqual(output, ["5"])
        self.assertEqual(symbols["y"].value, Decimal("5"))

    def test_output_string(self):
        self.assert_output('output<<"Hello World!"; output<<"";', ["Hello World!", ""])

    def test_output_variable_and_expression(self):
        self.assert_output("x:integer; y:double; x:=3; y:=1.25; output<<x; output<<x+y;", ["3", "4.25"])

    def test_case_insensitive_keywords_and_identifiers(self):
        self.assert_output('X:InTeGeR; x=3; If(X<5) Output<<x; OUTPUT<<"X If Output";', ["3", "X If Output"])

    def test_each_comparison_true_and_false(self):
        for operator, left, right in (("<", 2, 3), (">", 3, 2), ("==", 2, 2), ("!=", 2, 3)):
            with self.subTest(operator=operator):
                self.assert_output(f'if({left}{operator}{right}) output<<"yes";', ["yes"])
                false_left = right if operator != "==" else right + 1
                self.assert_output(f'if({false_left}{operator}{right}) output<<"no";', [])

    def test_condition_expressions_and_mixed_types(self):
        self.assert_output('if(1+2==4.25-1.25) output<<"equal";', ["equal"])

    def test_if_executes_one_statement(self):
        self.assert_output('if(3<2) output<<"skipped"; output<<"after";', ["after"])

    def test_if_assignment_and_nested_if(self):
        self.assert_output("x:integer; x:=2; if(x>1) x=x+3; if(x==5) if(x!=4) output<<x;", ["5"])

    def test_static_global_declaration_in_false_branch(self):
        self.assert_output("if(1>2) x:integer; output<<x;", ["0"])

    def test_empty_program(self):
        self.assert_output(" \n\t", [])

    def test_validation_errors(self):
        cases = (
            ("x:integer", "expected ';'"),
            ("x:integer; x:=1", "expected ';'"),
            ("output<<1", "expected ';'"),
            ("output<<x;", "undeclared variable"),
            ("x:=1;", "undeclared variable"),
            ("x:integer; X:double;", "redeclaration"),
            ("x:float;", "expected type"),
            ("x integer;", "expected ':'"),
            ("x:integer; x 5;", "for assignment"),
            ("x:integer; x:=;", "expected a number"),
            ("x:integer; x:=1+;", "expected a number"),
            ("if(1) output<<1;", "expected comparison"),
            ("if(1<) output<<1;", "expected a number"),
            ("if(1<2 output<<1;", "expected ')'"),
            ("if 1<2) output<<1;", "expected '('"),
            ("if(1<2)", "expected declaration"),
            ("output<1;", "expected '<<'"),
            ("output<<@;", "invalid token"),
            ("output<<1.2.3;", "invalid number"),
            ("output<<1.;", "invalid number"),
            ("output<<12abc;", "invalid number"),
            ('output<<"hello;', "unmatched string"),
            ('output<<"hello\nworld";', "unmatched string"),
            ("x:integer; x:=1.25;", "cannot assign double"),
            ("x:integer; x:=2.0;", "cannot assign double"),
            ("x:integer; y:double; x:=y;", "cannot assign double"),
            ("if(1>2) output<<missing;", "undeclared variable"),
            ("output<<x; x:integer;", "undeclared variable"),
        )
        for source, message in cases:
            with self.subTest(source=source):
                with self.assertRaisesRegex(HLError, message.replace("(", r"\(").replace(")", r"\)")):
                    execute(source)

    def test_token_locations_and_longest_symbols(self):
        tokens = Lexer("X: integer;\n Output<<X==5;").tokenize()
        self.assertEqual(tokens[0].value, "x")
        self.assertEqual((tokens[4].kind, tokens[4].line, tokens[4].column), ("OUTPUT", 2, 2))
        self.assertEqual([t.kind for t in tokens[5:9]], ["OUTPUT_OPERATOR", "IDENTIFIER", "EQUAL", "INTEGER_LITERAL"])

    def test_error_location(self):
        with self.assertRaisesRegex(HLError, "line 2, column 9: undeclared variable 'missing'"):
            execute("x:integer;\noutput<<missing;")

    def test_parser_builds_ast(self):
        program = Parser(Lexer("output<<8-3-2;").tokenize()).parse()
        self.assertIsInstance(program, Program)
        expression = program.statements[0].expression
        self.assertIsInstance(expression, BinaryExpression)
        self.assertIsInstance(expression.left, BinaryExpression)


class FileTests(unittest.TestCase):
    def run_source(self, directory, source):
        path = Path(directory) / "TEST.HL"
        path.write_text(source, encoding="utf-8")
        output = []
        status = run_file(path, output.append)
        return status, output

    def test_success_and_exact_artifact_format(self):
        with tempfile.TemporaryDirectory() as directory:
            status, output = self.run_source(directory, 'X: integer;\nX = 3 + 2;\nOutput << "Hello world";\n')
            self.assertEqual(status, 0)
            self.assertEqual(output, ["NO ERROR(S) FOUND", "Hello world"])
            root = Path(directory)
            self.assertEqual((root / "NOSPACES.TXT").read_text(), 'X:integer;\nX=3+2;\nOutput<<"Hello world";\n')
            self.assertEqual((root / "RES_SYM.TXT").read_text(),
                             "1:2\tCOLON\t:\n1:4\tINTEGER\tinteger\n1:11\tSEMICOLON\t;\n"
                             "2:3\tASSIGN\t=\n2:7\tPLUS\t+\n2:10\tSEMICOLON\t;\n"
                             "3:1\tOUTPUT\toutput\n3:8\tOUTPUT_OPERATOR\t<<\n3:24\tSEMICOLON\t;\n")

    def test_errors_create_artifacts_and_prevent_execution(self):
        for suffix in ("output<<@;", "output<<1", "output<<missing;"):
            with self.subTest(suffix=suffix), tempfile.TemporaryDirectory() as directory:
                status, output = self.run_source(directory, 'output<<"must not run";\n' + suffix)
                self.assertEqual(status, 1)
                self.assertEqual(output[0], "ERROR")
                self.assertEqual(len(output), 2)
                self.assertIn("line 2, column", output[1])
                self.assertTrue((Path(directory) / "NOSPACES.TXT").exists())
                self.assertTrue((Path(directory) / "RES_SYM.TXT").exists())

    def test_lexical_error_records_only_detected_tokens(self):
        with tempfile.TemporaryDirectory() as directory:
            self.run_source(directory, "x:integer; @ output<<1;")
            self.assertEqual((Path(directory) / "RES_SYM.TXT").read_text(),
                             "1:2\tCOLON\t:\n1:3\tINTEGER\tinteger\n1:10\tSEMICOLON\t;\n")

    def test_artifacts_are_replaced_on_next_run(self):
        with tempfile.TemporaryDirectory() as directory:
            self.run_source(directory, "x:integer; x:=5; output<<x;")
            self.run_source(directory, "")
            self.assertEqual((Path(directory) / "NOSPACES.TXT").read_text(), "")
            self.assertEqual((Path(directory) / "RES_SYM.TXT").read_text(), "")

    def test_missing_file_reports_error(self):
        with tempfile.TemporaryDirectory() as directory:
            output = []
            self.assertEqual(run_file(Path(directory) / "MISSING.HL", output.append), 1)
            self.assertEqual(output[0], "ERROR")

    def test_preprocessing_preserves_string_spaces(self):
        self.assertEqual(remove_spaces(' output << "a  b\tc" ;\n\tx := 5;'), 'output<<"a  b\tc";\nx:=5;')


if __name__ == "__main__":
    unittest.main()
