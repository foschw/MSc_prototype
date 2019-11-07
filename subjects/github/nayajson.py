from io import StringIO
import json
import unittest

class TestJsonTokenization(unittest.TestCase):

    def tokenize_sequence(self, string):
        return [token for token in tokenize(StringIO(string))]

    def tokenize_single_token(self, string):
        token_list = self.tokenize_sequence(string)
        self.assertEqual(1, len(token_list))
        _, token = token_list[0]
        return token

    def assertNumberEquals(self, expected, actual):
        token_list = self.tokenize_sequence(actual)
        self.assertEqual(1, len(token_list))
        ttype, token = token_list[0]
        self.assertEqual(expected, token)
        self.assertEqual(ttype, TOKEN_TYPE.NUMBER)

    def assertOperatorEquals(self, expected, actual):

        token_list = self.tokenize_sequence(actual)
        ttype, token = token_list[0]
        self.assertEqual(expected, token)
        self.assertEqual(ttype, TOKEN_TYPE.OPERATOR)

    def assertStringEquals(self, expected, actual):
        token_list = [token for token in tokenize(StringIO('"{}"'.format(actual)))]
        self.assertEqual(1, len(token_list))
        ttype, token = token_list[0]
        self.assertEqual(expected, token)
        self.assertEqual(ttype, TOKEN_TYPE.STRING)

    def test_number_parsing(self):
        self.assertNumberEquals(0, "0")
        self.assertNumberEquals(0.5, "0.5")
        self.assertNumberEquals(0, "-0")
        self.assertNumberEquals(12, "12")
        self.assertNumberEquals(3.5, "3.5")
        self.assertNumberEquals(1.2e11, "12e10")
        self.assertNumberEquals(7.8e-14, "78E-15")
        self.assertNumberEquals(0, "0e10")
        self.assertNumberEquals(65.7, "65.7")
        self.assertNumberEquals(892.978, "892.978")
        self.assertNumberEquals(8.9e7, "8.9E7")
        self.assertRaises(ValueError, self.tokenize_single_token, "01")
        self.assertRaises(ValueError, self.tokenize_single_token, "1.")
        self.assertRaises(ValueError, self.tokenize_single_token, "-01")
        self.assertRaises(ValueError, self.tokenize_single_token, "2a")
        self.assertRaises(ValueError, self.tokenize_single_token, "-a")
        self.assertRaises(ValueError, self.tokenize_single_token, "3.b")
        self.assertRaises(ValueError, self.tokenize_single_token, "3.e10")
        self.assertRaises(ValueError, self.tokenize_single_token, "3.6ea")
        self.assertRaises(ValueError, self.tokenize_single_token, "67.8e+a")

    def test_operator_parsing(self):
        self.assertOperatorEquals("{", "{")
        self.assertOperatorEquals("}", "}")
        self.assertOperatorEquals("[", "[")
        self.assertOperatorEquals("]", "]")
        self.assertOperatorEquals(":", ":")
        self.assertOperatorEquals(",", ",")

    def test_string_parsing(self):
        self.assertStringEquals("word", "word")
        self.assertStringEquals("with\tescape", "with\\tescape")
        self.assertStringEquals("with\n a different escape", "with\\n a different escape")
        self.assertStringEquals("using a \bbackspace", "using a \\bbackspace")
        self.assertStringEquals("now we have \f a formfeed", "now we have \\f a formfeed")
        self.assertStringEquals("\"a quote\"", "\\\"a quote\\\"")
        self.assertStringEquals("", "")
        self.assertStringEquals("/", "\\/")
        self.assertStringEquals("this char: \u0202", "this char: \\u0202")
        self.assertStringEquals("\uaf78", "\\uaf78")
        self.assertStringEquals("\u8A0b", "\\u8A0b")
        self.assertStringEquals("\ub3e7", "\\uB3e7")
        self.assertStringEquals("\u12ef", "\\u12eF")
        self.assertRaises(ValueError, self.tokenize_single_token, "\"\\uay76\"")
        self.assertRaises(ValueError, self.tokenize_single_token, "\"\\h\"")
        self.assertRaises(ValueError, self.tokenize_single_token, "\"\\2\"")
        self.assertRaises(ValueError, self.tokenize_single_token, "\"\\!\"")
        self.assertRaises(ValueError, self.tokenize_single_token, "\"\\u!\"")

    def test_sequence(self):
        result = [token for token in tokenize(StringIO("123 \"abc\":{}"))]
        self.assertEqual(result, [(2, 123), (1, 'abc'), (0, ':'), (0, '{'), (0, '}')])

        # Borrowed from http://en.wikipedia.org/wiki/JSON
        big_file = """{
          "firstName": "John",
          "lastName": "Smith",
          "isAlive": true,
          "age": 25,
          "height_cm": 167.6,
          "address": {
            "streetAddress": "21 2nd Street",
            "city": "New York",
            "state": "NY",
            "postalCode": "10021-3100"
          },
          "phoneNumbers": [
            {
              "type": "home",
              "number": "212 555-1234"
            },
            {
              "type": "office",
              "number": "646 555-4567"
            }
          ],
          "children": [],
          "spouse": null
        }"""
        result = [token for token in tokenize(StringIO(big_file))]
        expected = [(0, '{'), (1, 'firstName'), (0, ':'), (1, 'John'), (0, ','), (1, 'lastName'), (0, ':'),
                    (1, 'Smith'), (0, ','), (1, 'isAlive'), (0, ':'), (3, True), (0, ','), (1, 'age'), (0, ':'),
                    (2, 25), (0, ','), (1, 'height_cm'), (0, ':'), (2, 167.6), (0, ','), (1, 'address'), (0, ':'),
                    (0, '{'), (1, 'streetAddress'), (0, ':'), (1, '21 2nd Street'), (0, ','), (1, 'city'), (0, ':'),
                    (1, 'New York'), (0, ','), (1, 'state'), (0, ':'), (1, 'NY'), (0, ','), (1, 'postalCode'),
                    (0, ':'), (1, '10021-3100'), (0, '}'), (0, ','), (1, 'phoneNumbers'), (0, ':'), (0, '['), (0, '{'),
                    (1, 'type'), (0, ':'), (1, 'home'), (0, ','), (1, 'number'), (0, ':'), (1, '212 555-1234'),
                    (0, '}'), (0, ','), (0, '{'), (1, 'type'), (0, ':'), (1, 'office'), (0, ','), (1, 'number'),
                    (0, ':'), (1, '646 555-4567'), (0, '}'), (0, ']'), (0, ','), (1, 'children'), (0, ':'), (0, '['),
                    (0, ']'), (0, ','), (1, 'spouse'), (0, ':'), (4, None), (0, '}')]
        self.assertListEqual(result, expected)
        big_file_no_space = '{"firstName":"John","lastName":"Smith","isAlive":true,"age":25,"height_cm":167.6,"addres' \
                            's":{"streetAddress":"21 2nd Street","city":"New York","state":"NY","postalCode":"10021-3' \
                            '100"},"phoneNumbers":[{"type":"home","number":"212 555-1234"},{"type":"office","number":' \
                            '"646 555-4567"}],"children":[],"spouse":null}'
        result = [token for token in tokenize(StringIO(big_file_no_space))]
        self.assertListEqual(result, expected)
        result = [token for token in tokenize(StringIO("854.6,123"))]
        self.assertEqual(result, [(2, 854.6), (0, ','), (2, 123)])
        self.assertRaises(ValueError, self.tokenize_sequence, "123\"text\"")
        self.assertRaises(ValueError, self.tokenize_sequence, "23.9e10true")
        self.assertRaises(ValueError, self.tokenize_sequence, "\"test\"56")

    def test_arrays(self):
        arr = parse_string('[]')
        self.assertListEqual(arr, [])
        arr = parse_string('["People", "Places", "Things"]')
        self.assertListEqual(arr, ["People", "Places", "Things"])
        arr = parse_string('["Apples", "Bananas", ["Pears", "Limes"]]')
        self.assertListEqual(arr, ["Apples", "Bananas", ["Pears", "Limes"]])
        self.assertRaises(ValueError, parse_string, '["People", "Places", "Things"')
        self.assertRaises(ValueError, parse_string, '["People", "Places" "Things"]')
        self.assertRaises(ValueError, parse_string, '["People", "Places"] "Things"]')

    def test_objects(self):
        obj = parse_string('{"key1":"value1"}')
        self.assertDictEqual(obj, {"key1": "value1"})

        obj = parse_string("{}")
        self.assertDictEqual(obj, {})

        obj = parse_string('{"name": {"first":"Daniel", "last": "Yule"}}')
        self.assertDictEqual(obj, {"name": {"first": "Daniel", "last": "Yule"}})

        # Borrowed from http://en.wikipedia.org/wiki/JSON
        big_file = """{
          "firstName": "John",
          "lastName": "Smith",
          "isAlive": true,
          "age": 25,
          "height_cm": 167.6,
          "address": {
            "streetAddress": "21 2nd Street",
            "city": "New York",
            "state": "NY",
            "postalCode": "10021-3100"
          },
          "phoneNumbers": [
            {
              "type": "home",
              "number": "212 555-1234"
            },
            {
              "type": "office",
              "number": "646 555-4567"
            }
          ],
          "children": [],
          "spouse": null
        }"""
        obj = parse_string(big_file)
        self.assertDictEqual(obj, {
            "firstName": "John",
            "lastName": "Smith",
            "isAlive": True,
            "age": 25,
            "height_cm": 167.6,
            "address": {
                "streetAddress": "21 2nd Street",
                "city": "New York",
                "state": "NY",
                "postalCode": "10021-3100"
            },
            "phoneNumbers": [
                {
                    "type": "home",
                    "number": "212 555-1234"
                },
                {
                    "type": "office",
                    "number": "646 555-4567"
                }
            ],
            "children": [],
            "spouse": None
        })

        self.assertRaises(ValueError, parse_string, "{")
        self.assertRaises(ValueError, parse_string, '{"key": "value"')
        self.assertRaises(ValueError, parse_string, '{"key": "value"}}')
        self.assertRaises(ValueError, parse_string, '{"key": "value", "value2"}')
        self.assertRaises(ValueError, parse_string, '{"key", "value": "value2"}')
        self.assertRaises(ValueError, parse_string, '{"key", "value": "value2"]}')
        self.assertRaises(ValueError, parse_string, '{"key", "value": "value2" []}')
        self.assertRaises(ValueError, parse_string, '{"key", "value": ["value2"]}')

    def test_array_stream(self):
        arr = stream_array(tokenize(StringIO('[]')))
        self.assertListEqual([i for i in arr], [])
        arr = stream_array(tokenize(StringIO('["People", "Places", "Things"]')))
        self.assertListEqual([i for i in arr], ["People", "Places", "Things"])
        arr = stream_array(tokenize(StringIO('["Apples", "Bananas", ["Pears", "Limes"]]')))
        self.assertListEqual([i for i in arr], ["Apples", "Bananas", ["Pears", "Limes"]])
        arr = stream_array(tokenize(StringIO('["Apples", ["Pears", "Limes"], "Bananas"]')))
        self.assertListEqual([i for i in arr], ["Apples", ["Pears", "Limes"], "Bananas"])
        arr = stream_array(tokenize(StringIO('["Apples", {"key":"value"}, "Bananas"]')))
        self.assertListEqual([i for i in arr], ["Apples", {"key": "value"}, "Bananas"])

    def test_large_sample(self):
        with open("../sample.json", "r", encoding="utf-8") as file:
            obj2 = json.load(file)
        with open("../sample.json", "r", encoding="utf-8") as file:
            obj = parse(file)

        self.assertDictEqual(obj, obj2)

class TOKEN_TYPE:
    OPERATOR = 0
    STRING = 1
    NUMBER = 2
    BOOLEAN = 3
    NULL = 4


class __TOKENIZER_STATE:
    WHITESPACE = 0
    INTEGER_0 = 1
    INTEGER_SIGN = 2
    INTEGER = 3
    INTEGER_EXP = 4
    INTEGER_EXP_0 = 5
    FLOATING_POINT_0 = 6
    FLOATING_POINT = 8
    STRING = 9
    STRING_ESCAPE = 10
    STRING_END = 11
    TRUE_1 = 12
    TRUE_2 = 13
    TRUE_3 = 14
    FALSE_1 = 15
    FALSE_2 = 16
    FALSE_3 = 17
    FALSE_4 = 18
    NULL_1 = 19
    NULL_2 = 20
    NULL_3 = 21
    UNICODE_1 = 22
    UNICODE_2 = 23
    UNICODE_3 = 24
    UNICODE_4 = 25


def tokenize(stream):
    def is_delimiter(char):
        return char.isspace() or char in "{}[]:,"

    token = []
    charcode = 0
    completed = False
    now_token = ""

    def process_char(char, charcode):
        nonlocal token, completed, now_token
        advance = True
        add_char = False
        next_state = state
        if state == __TOKENIZER_STATE.WHITESPACE:
            if char == "{":
                completed = True
                now_token = (TOKEN_TYPE.OPERATOR, "{")
            elif char == "}":
                completed = True
                now_token = (TOKEN_TYPE.OPERATOR, "}")
            elif char == "[":
                completed = True
                now_token = (TOKEN_TYPE.OPERATOR, "[")
            elif char == "]":
                completed = True
                now_token = (TOKEN_TYPE.OPERATOR, "]")
            elif char == ",":
                completed = True
                now_token = (TOKEN_TYPE.OPERATOR, ",")
            elif char == ":":
                completed = True
                now_token = (TOKEN_TYPE.OPERATOR, ":")
            elif char == "\"":
                next_state = __TOKENIZER_STATE.STRING
            elif char in "123456789":
                next_state = __TOKENIZER_STATE.INTEGER
                add_char = True
            elif char == "0":
                next_state = __TOKENIZER_STATE.INTEGER_0
                add_char = True
            elif char == "-":
                next_state = __TOKENIZER_STATE.INTEGER_SIGN
                add_char = True
            elif char == "f":
                next_state = __TOKENIZER_STATE.FALSE_1
            elif char == "t":
                next_state = __TOKENIZER_STATE.TRUE_1
            elif char == "n":
                next_state = __TOKENIZER_STATE.NULL_1
            elif not char.isspace():
                raise ValueError("Invalid JSON character: '{0}'".format(char))
        elif state == __TOKENIZER_STATE.INTEGER:
            if char in "0123456789":
                add_char = True
            elif char == ".":
                next_state = __TOKENIZER_STATE.FLOATING_POINT_0
                add_char = True
            elif char == "e" or char == 'E':
                next_state = __TOKENIZER_STATE.INTEGER_EXP_0
                add_char = True
            elif is_delimiter(char):
                next_state = __TOKENIZER_STATE.WHITESPACE
                completed = True
                now_token = (TOKEN_TYPE.NUMBER, int("".join(token)))
                advance = False
            else:
                raise ValueError("A number must contain only digits.  Got '{}'".format(char))
        elif state == __TOKENIZER_STATE.INTEGER_0:
            if char == ".":
                next_state = __TOKENIZER_STATE.FLOATING_POINT_0
                add_char = True
            elif char == "e" or char == 'E':
                next_state = __TOKENIZER_STATE.INTEGER_EXP_0
                add_char = True
            elif is_delimiter(char):
                next_state = __TOKENIZER_STATE.WHITESPACE
                completed = True
                now_token = (TOKEN_TYPE.NUMBER, 0)
                advance = False
            else:
                raise ValueError("A 0 must be followed by a '.' or a 'e'.  Got '{0}'".format(char))
        elif state == __TOKENIZER_STATE.INTEGER_SIGN:
            if char == "0":
                next_state = __TOKENIZER_STATE.INTEGER_0
                add_char = True
            elif char in "123456789":
                next_state = __TOKENIZER_STATE.INTEGER
                add_char = True
            else:
                raise ValueError("A - must be followed by a digit.  Got '{0}'".format(char))
        elif state == __TOKENIZER_STATE.INTEGER_EXP_0:
            if char == "+" or char == "-" or char in "0123456789":
                next_state = __TOKENIZER_STATE.INTEGER_EXP
                add_char = True
            else:
                raise ValueError("An e in a number must be followed by a '+', '-' or digit.  Got '{0}'".format(char))
        elif state == __TOKENIZER_STATE.INTEGER_EXP:
            if char in "0123456789":
                add_char = True
            elif is_delimiter(char):
                completed = True
                now_token = (TOKEN_TYPE.NUMBER, float("".join(token)))
                next_state = __TOKENIZER_STATE.WHITESPACE
                advance = False
            else:
                raise ValueError("A number exponent must consist only of digits.  Got '{}'".format(char))
        elif state == __TOKENIZER_STATE.FLOATING_POINT:
            if char in "0123456789":
                add_char = True
            elif char == "e" or char == "E":
                next_state = __TOKENIZER_STATE.INTEGER_EXP_0
                add_char = True
            elif is_delimiter(char):
                completed = True
                now_token = (TOKEN_TYPE.NUMBER, float("".join(token)))
                next_state = __TOKENIZER_STATE.WHITESPACE
                advance = False
            else:
                raise ValueError("A number must include only digits")
        elif state == __TOKENIZER_STATE.FLOATING_POINT_0:
            if char in "0123456789":
                next_state = __TOKENIZER_STATE.FLOATING_POINT
                add_char = True
            else:
                raise ValueError("A number with a decimal point must be followed by a fractional part")
        elif state == __TOKENIZER_STATE.FALSE_1:
            if char == "a":
                next_state = __TOKENIZER_STATE.FALSE_2
            else:
                raise ValueError("Invalid JSON character: '{0}'".format(char))
        elif state == __TOKENIZER_STATE.FALSE_2:
            if char == "l":
                next_state = __TOKENIZER_STATE.FALSE_3
            else:
                raise ValueError("Invalid JSON character: '{0}'".format(char))
        elif state == __TOKENIZER_STATE.FALSE_3:
            if char == "s":
                next_state = __TOKENIZER_STATE.FALSE_4
            else:
                raise ValueError("Invalid JSON character: '{0}'".format(char))
        elif state == __TOKENIZER_STATE.FALSE_4:
            if char == "e":
                next_state = __TOKENIZER_STATE.WHITESPACE
                completed = True
                now_token = (TOKEN_TYPE.BOOLEAN, False)
            else:
                raise ValueError("Invalid JSON character: '{0}'".format(char))
        elif state == __TOKENIZER_STATE.TRUE_1:
            if char == "r":
                next_state = __TOKENIZER_STATE.TRUE_2
            else:
                raise ValueError("Invalid JSON character: '{0}'".format(char))
        elif state == __TOKENIZER_STATE.TRUE_2:
            if char == "u":
                next_state = __TOKENIZER_STATE.TRUE_3
            else:
                raise ValueError("Invalid JSON character: '{0}'".format(char))
        elif state == __TOKENIZER_STATE.TRUE_3:
            if char == "e":
                next_state = __TOKENIZER_STATE.WHITESPACE
                completed = True
                now_token = (TOKEN_TYPE.BOOLEAN, True)
            else:
                raise ValueError("Invalid JSON character: '{0}'".format(char))
        elif state == __TOKENIZER_STATE.NULL_1:
            if char == "u":
                next_state = __TOKENIZER_STATE.NULL_2
            else:
                raise ValueError("Invalid JSON character: '{0}'".format(char))
        elif state == __TOKENIZER_STATE.NULL_2:
            if char == "l":
                next_state = __TOKENIZER_STATE.NULL_3
            else:
                raise ValueError("Invalid JSON character: '{0}'".format(char))
        elif state == __TOKENIZER_STATE.NULL_3:
            if char == "l":
                next_state = __TOKENIZER_STATE.WHITESPACE
                completed = True
                now_token = (TOKEN_TYPE.NULL, None)
            else:
                raise ValueError("Invalid JSON character: '{0}'".format(char))
        elif state == __TOKENIZER_STATE.STRING:
            if char == "\"":
                completed = True
                now_token = (TOKEN_TYPE.STRING, "".join(token))
                next_state = __TOKENIZER_STATE.STRING_END
            elif char == "\\":
                next_state = __TOKENIZER_STATE.STRING_ESCAPE
            else:
                add_char = True
        elif state == __TOKENIZER_STATE.STRING_END:
            if is_delimiter(char):
                advance = False
                next_state = __TOKENIZER_STATE.WHITESPACE
            else:
                raise ValueError("Expected whitespace or an operator after strin.  Got '{}'".format(char))
        elif state == __TOKENIZER_STATE.STRING_ESCAPE:
            next_state = __TOKENIZER_STATE.STRING
            if char == "\\" or char == "\"":
                add_char = True
            elif char == "b":
                char = "\b"
                add_char = True
            elif char == "f":
                char = "\f"
                add_char = True
            elif char == "n":
                char = "\n"
                add_char = True
            elif char == "t":
                char = "\t"
                add_char = True
            elif char == "r":
                char = "\r"
                add_char = True
            elif char == "/":
                char = "/"
                add_char = True
            elif char == "u":
                next_state = __TOKENIZER_STATE.UNICODE_1
                charcode = 0
            else:
                raise ValueError("Invalid string escape: {}".format(char))
        elif state == __TOKENIZER_STATE.UNICODE_1:
            if char in "0123456789":
                charcode = (ord(char) - 48) * 4096
            elif char in "abcdef":
                charcode = (ord(char) - 87) * 4096
            elif char in "ABCDEF":
                charcode = (ord(char) - 55) * 4096
            else:
                raise ValueError("Invalid character code: {}".format(char))
            next_state = __TOKENIZER_STATE.UNICODE_2
            char = ""
        elif state == __TOKENIZER_STATE.UNICODE_2:
            if char in "0123456789":
                charcode += (ord(char) - 48) * 256
            elif char in "abcdef":
                charcode += (ord(char) - 87) * 256
            elif char in "ABCDEF":
                charcode += (ord(char) - 55) * 256
            else:
                raise ValueError("Invalid character code: {}".format(char))
            next_state = __TOKENIZER_STATE.UNICODE_3
            char = ""
        elif state == __TOKENIZER_STATE.UNICODE_3:
            if char in "0123456789":
                charcode += (ord(char) - 48) * 16
            elif char in "abcdef":
                charcode += (ord(char) - 87) * 16
            elif char in "ABCDEF":
                charcode += (ord(char) - 55) * 16
            else:
                raise ValueError("Invalid character code: {}".format(char))
            next_state = __TOKENIZER_STATE.UNICODE_4
            char = ""
        elif state == __TOKENIZER_STATE.UNICODE_4:
            if char in "0123456789":
                charcode += ord(char) - 48
            elif char in "abcdef":
                charcode += ord(char) - 87
            elif char in "ABCDEF":
                charcode += ord(char) - 55
            else:
                raise ValueError("Invalid character code: {}".format(char))
            next_state = __TOKENIZER_STATE.STRING
            char = chr(charcode)
            add_char = True

        if add_char:
            token.append(char)

        return advance, next_state, charcode
    state = __TOKENIZER_STATE.WHITESPACE
    char = stream.read(1)
    index = 0
    while char:
        try:
            advance, state, charcode = process_char(char, charcode)
        except ValueError as e:
            raise ValueError("".join([e.args[0], " at index {}".format(index)]))
        if completed:
            completed = False
            token = []
            yield now_token
        if advance:
            char = stream.read(1)
            index += 1
    process_char(" ", charcode)
    if completed:
        yield now_token


def parse_string(string):
    return parse(StringIO(string))

def parse(file):
    token_stream = tokenize(file)
    val, token_type, token = __parse(token_stream, next(token_stream))
    if token is not None:
        raise ValueError("Improperly closed JSON object")
    try:
        next(token_stream)
    except StopIteration:
        return val
    raise ValueError("Additional string after end of JSON")
    


def __parse(token_stream, first_token):
    class KVP:
        def __init__(self, key):
            self.key = key
            self.value = None
            self.set = False

        def __str__(self):
            if self.set:
                return "{}: {}".format(self.key, self.value)
            else:
                return "{}: <NULL>".format(self.key)

    stack = []
    token_type, token = first_token
    if token_type == TOKEN_TYPE.OPERATOR:
        if token == "{":
            stack.append({})
        elif token == "[":
            stack.append([])
        else:
            raise ValueError("Expected object or array.  Got '{}'".format(token))
    else:
        raise ValueError("Expected object or array.  Got '{}'".format(token))

    last_type, last_token = token_type, token
    try:
        token_type, token = next(token_stream)
    except StopIteration as e:
        raise ValueError("Too many opening braces") from e
    try:
        while True:
            if isinstance(stack[-1], list):
                if last_type == TOKEN_TYPE.OPERATOR:
                    if last_token == "[":
                        if token_type == TOKEN_TYPE.OPERATOR:
                            if token == "{":
                                stack.append({})
                            elif token == "[":
                                stack.append([])
                            elif token != "]":
                                raise ValueError("Array must either be empty or contain a value.  Got '{}'".
                                                 format(token))
                        else:
                            stack.append(token)
                    elif last_token == ",":
                        if token_type == TOKEN_TYPE.OPERATOR:
                            if token == "{":
                                stack.append({})
                            elif token == "[":
                                stack.append([])
                            else:
                                raise ValueError("Array value expected.  Got '{}'".format(token))
                        else:
                            stack.append(token)
                    elif last_token == "]":
                        value = stack.pop()
                        if len(stack) == 0:
                            return value, token_type, token
                        if isinstance(stack[-1], list):
                            stack[-1].append(value)
                        elif isinstance(stack[-1], dict):
                            stack[-1][value.key] = value.value
                        elif isinstance(stack[-1], KVP):
                            stack[-1].value = value
                            stack[-1].set = True
                            value = stack.pop()
                            if len(stack) == 0:
                                return value, token_type, token
                            if isinstance(stack[-1], list):
                                stack[-1].append(value)
                            elif isinstance(stack[-1], dict):
                                stack[-1][value.key] = value.value
                            else:
                                raise ValueError("Array items must be followed by a comma or closing bracket.  "
                                                 "Got '{}'".format(value))
                        else:
                            raise ValueError("Array items must be followed by a comma or closing bracket.  "
                                             "Got '{}'".format(value))
                    elif last_token == "}":
                        raise ValueError("Array closed with a '}'")
                    else:
                        raise ValueError("Array should not contain ':'")
                else:
                    raise ValueError("Unknown Error")
            elif isinstance(stack[-1], dict):
                if last_type == TOKEN_TYPE.OPERATOR:
                    if last_token == "{":
                        if token_type == TOKEN_TYPE.OPERATOR:
                            if token == "{":
                                stack.append({})
                            elif token == "[":
                                stack.append([])
                            elif token != "}":
                                raise ValueError("Object must either be empty or contain key value pairs."
                                                 "  Got '{}'".format(token))
                        elif token_type == TOKEN_TYPE.STRING:
                            stack.append(KVP(token))
                        else:
                            raise ValueError("Object keys must be strings.  Got '{}'".format(token))
                    elif last_token == ",":
                        if token_type == TOKEN_TYPE.OPERATOR:
                            if token == "{":
                                stack.append({})
                            elif token == "[":
                                stack.append([])
                            else:
                                raise ValueError("Object key expected.  Got '{}'".format(token))
                        elif token_type == TOKEN_TYPE.STRING:
                            stack.append(KVP(token))
                        else:
                            raise ValueError("Object keys must be strings.  Got '{}'".format(token))
                    elif last_token == "}":
                        value = stack.pop()
                        if len(stack) == 0:
                            return value, token_type, token
                        if isinstance(stack[-1], list):
                            stack[-1].append(value)
                        elif isinstance(stack[-1], dict):
                            stack[-1][value.key] = value.value
                        elif isinstance(stack[-1], KVP):
                            stack[-1].value = value
                            stack[-1].set = True
                            value = stack.pop()
                            if len(stack) == 0:
                                return value, token_type, token
                            if isinstance(stack[-1], list):
                                stack[-1].append(value)
                            elif isinstance(stack[-1], dict):
                                stack[-1][value.key] = value.value
                            else:
                                raise ValueError("Object key value pairs must be followed by a comma or "
                                                 "closing bracket.  Got '{}'".format(value))
                    elif last_token == "]":
                        raise ValueError("Object closed with a ']'")
                    else:
                        raise ValueError("Object key value pairs should be separated by comma, not ':'")
            elif isinstance(stack[-1], KVP):
                if stack[-1].set:
                    if token_type == TOKEN_TYPE.OPERATOR:
                        if token != "}" and token != ",":
                            raise ValueError("Object key value pairs should be followed by ',' or '}'.  Got '"
                                             + token + "'")
                        value = stack.pop()
                        if len(stack) == 0:
                            return value, token_type, token
                        if isinstance(stack[-1], list):
                            stack[-1].append(value)
                        elif isinstance(stack[-1], dict):
                            stack[-1][value.key] = value.value
                        else:
                            raise ValueError("Object key value pairs must be followed by a comma or closing bracket.  "
                                             "Got '{}'".format(value))
                        if token == "}" and len(stack) == 1:
                            return stack[0], None, None
                    else:
                        raise ValueError("Object key value pairs should be followed by ',' or '}'.  Got '"
                                         + token + "'")
                else:
                    if token_type == TOKEN_TYPE.OPERATOR and token == ":" and last_type == TOKEN_TYPE.STRING:
                        pass
                    elif last_type == TOKEN_TYPE.OPERATOR and last_token == ":":
                        if token_type == TOKEN_TYPE.OPERATOR:
                            if token == "{":
                                stack.append({})
                            elif token == "[":
                                stack.append([])
                            else:
                                raise ValueError("Object property value expected.  Got '{}'".format(token))
                        else:
                            stack[-1].value = token
                            stack[-1].set = True
                    else:
                        raise ValueError("Object keys must be separated from values by a single ':'.  "
                                         "Got '{}'".format(token))
            else:
                value = stack.pop()
                if isinstance(stack[-1], list):
                    stack[-1].append(value)
                elif isinstance(stack[-1], dict):
                    stack[-1][value.key] = value.value
                else:
                    raise ValueError("Array items must be followed by a comma or closing bracket.  "
                                     "Got '{}'".format(value))

            last_type, last_token = token_type, token
            token_type, token = next(token_stream)
    except StopIteration as e:
        if len(stack) == 1:
            return stack[0], None, None
        else:
            raise ValueError("JSON Object not properly closed") from e


def stream_array(token_stream):

    def process_token(token_type, token):
        if token_type == TOKEN_TYPE.OPERATOR:
            if token == ']':
                return None, None, None
            elif token == ",":
                token_type, token = next(token_stream)
                if token_type == TOKEN_TYPE.OPERATOR:
                    if token == "[" or token == "{":
                        return __parse(token_stream, (token_type, token))
                    else:
                        raise ValueError("Expected an array value.  Got '{}'".format(token))
                else:
                    return token, None, None
            else:
                raise ValueError("Array entries must be followed by ',' or ']'.  Got '{}'".format(token))
        else:
            return token, None, None

    token_type, token = next(token_stream)
    if token_type != TOKEN_TYPE.OPERATOR or token != '[':
        raise ValueError("Array must start with '['.  Got '{}'".format(token))

    token_type, token = next(token_stream)
    while True:
        while token is not None:
            value, token_type, token  = process_token(token_type, token)
            if value is None:
                return
            yield value
        token_type, token = next(token_stream)

def main(input):
    return parse_string(input)

if __name__ == "__main__":
    import sys
    print(main(sys.argv[1]))