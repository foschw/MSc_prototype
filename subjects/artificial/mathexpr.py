# A really simple expression evaluator supporting the
# four basic math functions, parentheses, and variables.
# source: https://github.com/vrthra/pychains
# Augmented with a simple test suite
import unittest

class TestMathexpr(unittest.TestCase):
    def test_pi_const(self):
        with self.assertRaises(TypeError):
            parser = Parser("", vars={"pi":"3"})

    def test_e_const(self):
        with self.assertRaises(TypeError) as ex:
            parser = Parser("", vars={"e":"3"})

    def test_priority(self):
        self.assertEqual(Parser("2+3*4").getValue(),14)

    def test_ignore_whitespace(self):
        self.assertEqual(Parser("\t2*\n3").getValue(),6)

    def test_invalid_char(self):
        with self.assertRaises(TypeError):
            Parser("2*?").getValue()

    def test_div_by_zero(self):
        with self.assertRaises(TypeError):
            Parser("pi/0").getValue()

    def test_parentheses_unbalanced(self):
        with self.assertRaises(Exception) as ex:
            Parser("(2*(3+4)))").getValue()
        self.assertEqual(type(ex.exception), Exception)

    def test_unbound_var(self):
        with self.assertRaises(TypeError):
            Parser("2*a").getValue()

    def test_multiple_dot(self):
        with self.assertRaises(Exception) as ex:
            Parser("2.45.6").getValue()
        self.assertEqual(type(ex.exception), Exception)

    def test_neg_1(self):
        self.assertEqual(Parser("2*-21").getValue(),-42)

    def test_neg_2(self):
        self.assertEqual(Parser("-3*4").getValue(),-12)

    def test_neg_3(self):
        self.assertEqual(Parser("-6*-5").getValue(),30)

    def test_float_1(self):
        self.assertEqual(Parser("5*3.2").getValue(), 16.0)

    def test_float_2(self):
        self.assertEqual(Parser("3.2+2.7").getValue(), 5.9)

    def test_int_1(self):
        self.assertEqual(Parser("3+4*5-6/6").getValue(),22)

    def test_int_2(self):
        self.assertEqual(Parser("3*4+5-6").getValue(), 11)

    def test_omitted_dot_1(self):
        self.assertEqual(Parser(".3*0.2").getValue(),0.06)

    def test_omitted_dot_2(self):
        self.assertEqual(Parser("3*.5").getValue(),1.5)

class Parser:
    def __init__(self, string, vars={}):
        self.string = string
        self.index = 0
        self.vars = {
            'pi': 3.141592653589793,
            'e': 2.718281828459045
        }
        for var in vars.keys():
            if self.getVarValue(var) != None:
                raise Exception("Cannot redefine the value of " + var)
            self.vars[var] = vars[var]

    def hasVar(self, v):
        for k in self.vars.keys():
            if v == k:
                return True
        return False

    def getVarValue(self, v, default):
        if not self.hasVar(v): return default
        return self.vars[v]

    def getValue(self):
        value = self.parseExpression()
        self.skipWhitespace()
        if self.hasNext():
            raise Exception(
                "Unexpected character found: '" +
                self.peek() +
                "' at index " +
                str(self.index))
        return value

    def peek(self):
        return self.string[self.index:self.index + 1]

    def hasNext(self):
        return self.string[self.index:] != ''

    def skipWhitespace(self):
        while self.hasNext():
            if self.peek() in ' \t\n\r':
                self.index += 1
            else:
                return

    def parseExpression(self):
        return self.parseAddition()

    def parseAddition(self):
        values = [self.parseMultiplication()]
        while True:
            self.skipWhitespace()
            char = self.peek()
            if char == '+':
                self.index += 1
                values.append(self.parseMultiplication())
            elif char == '-':
                self.index += 1
                values.append(-1 * self.parseMultiplication())
            else:
                break
        return sum(values)

    def parseMultiplication(self):
        values = [self.parseParenthesis()]
        while True:
            self.skipWhitespace()
            char = self.peek()
            if char == '*':
                self.index += 1
                values.append(self.parseParenthesis())
            elif char == '/':
                div_index = self.index
                self.index += 1
                denominator = self.parseParenthesis()
                if denominator == 0:
                    raise Exception(
                        "Division by 0 kills baby whales (occured at index " +
                        str(div_index) +
                        ")")
                values.append(1.0 / denominator)
            else:
                break
        value = 1.0
        for factor in values:
            value *= factor
        return value

    def parseParenthesis(self):
        self.skipWhitespace()
        char = self.peek()
        if char == '(':
            self.index += 1
            value = self.parseExpression()
            self.skipWhitespace()
            if self.peek() != ')':
                raise Exception(
                    "No closing parenthesis found at character "
                    + str(self.index))
            self.index += 1
            return value
        else:
            return self.parseNegative()

    def parseNegative(self):
        self.skipWhitespace()
        char = self.peek()
        if char == '-':
            self.index += 1
            return -1 * self.parseParenthesis()
        else:
            return self.parseValue()

    def parseValue(self):
        self.skipWhitespace()
        char = self.peek()
        if char in ('0123456789.'):
            return self.parseNumber()
        else:
            return self.parseVariable()

    def parseVariable(self):
        self.skipWhitespace()
        var = None
        while self.hasNext():
            char = self.peek()
            if char.lower() in '_abcdefghijklmnopqrstuvwxyz0123456789':
                var += char
                self.index += 1
            else:
                break

        value = self.getVarValue(var, None)
        if value == None:
            raise Exception(
                "Unrecognized variable: '" +
                var +
                "'")
        return float(value)

    def parseNumber(self):
        self.skipWhitespace()
        strValue = ''
        decimal_found = False
        char = None

        while self.hasNext():
            char = self.peek()
            if char == '.':
                if decimal_found:
                    raise Exception(
                        "Found an extra period in a number at character " +
                        str(self.index) +
                        ". Are you European?")
                decimal_found = True
                strValue += '.'
            elif char in '0123456789':
                strValue += char
            else:
                break
            self.index += 1

        if len(strValue) == 0:
            if char == '':
                raise Exception("Unexpected end found")
            else:
                raise Exception(
                    "I was expecting to find a number at character " +
                    str(self.index) +
                    " but instead I found a '" +
                    char +
                    "'. What's up with that?")

        return float(strValue)

        # p = Parser(expression, vars)

def main(s):
    parse = Parser(s)
    # if s in ["a", "b", "c"]:
    #     return
    return parse.getValue()

if __name__ == "__main__":
    import sys
    main(sys.argv[1])
