import math
import io
import types
__pychecker__ = 'no-returnvalues'
WS = set([' ', '\t', '\r', '\n', '\b', '\f'])
DIGITS = set([str(i)for i in range(0, 10)])
NUMSTART = DIGITS.union(['.', '-', '+'])
NUMCHARS = NUMSTART.union(['e', 'E'])
ESC_MAP = {'n': '\n', 't': '\t', 'r': '\r', 'b': '\b', 'f': '\f'}
REV_ESC_MAP = dict([(_v, _k)for _k, _v in list(ESC_MAP.items())]+[('"', '"')])
E_BYTES = 'input string must be type str containing ASCII or UTF-8 bytes'
E_MALF = 'malformed JSON data'
E_TRUNC = 'truncated JSON data'
E_BOOL = 'expected boolean'
E_NULL = 'expected null'
E_LITEM = 'expected list item'
E_DKEY = 'expected key'
E_COLON = 'missing colon after key'
E_EMPTY = 'found empty string, not valid JSON data'
E_BADESC = 'bad escape character found'
E_UNSUPP = 'unsupported type "%s" cannot be JSON-encoded'
E_BADFLOAT = 'cannot emit floating point value "%s"'
NEG_INF = float('-inf')
POS_INF = float('inf')


class JSONError(Exception):
    def __init__(self, msg, stm=None, pos=0):
        if stm:
            msg += ' at position %d, "%s"' % (pos, repr(stm.substr(pos, 32)))
        Exception.__init__(self, msg)


class JSONStream(object):
    def __init__(self, data):
        self._stm = io.StringIO(data)

    @property
    def pos(self):
        return self._stm.tell()

    @property
    def len(self):
        return len(self._stm.getvalue())

    def getvalue(self):
        return self._stm.getvalue()

    def skipspaces(self):
        self._skip(lambda c: c not in WS)

    def _skip(self, stopcond):
        while True:
            c = self.peek()
            if stopcond(c)or c == '':
                break
            next(self)

    def __next__(self, size=1):
        return self._stm.read(size)

    def next_ord(self):
        return ord(next(self))

    def peek(self):
        if self.pos == self.len:
            return ''
        return self.getvalue()[self.pos]

    def substr(self, pos, length):
        return self.getvalue()[pos:pos+length]


def _decode_utf8(c0, stm):
    c0 = ord(c0)
    r = 0xFFFD
    nc = stm.next_ord
    if(c0 & 0xE0) == 0xC0:
        r = ((c0 & 0x1F) << 6)+(nc() & 0x3F)
    elif(c0 & 0xF0) == 0xE0:
        r = ((c0 & 0x0F) << 12)+((nc() & 0x3F) << 6)+(nc() & 0x3F)
    elif(c0 & 0xF8) == 0xF0:
        r = ((c0 & 0x07) << 18)+((nc() & 0x3F) << 12) + \
            ((nc() & 0x3F) << 6)+(nc() & 0x3F)
    return chr(r)


def decode_escape(c, stm):
    v = ESC_MAP.get(c, None)
    if v is not None:
        return v
    elif c != 'u':
        return c
    sv = 12
    r = 0
    for _ in range(0, 4):
        r |= int(next(stm), 16) << sv
        sv -= 4
    return chr(r)


def _from_json_string(stm):
    next(stm)
    r = []
    while True:
        c = next(stm)
        if c == '':
            raise JSONError(E_TRUNC, stm, stm.pos-1)
        elif c == '\\':
            c = next(stm)
            r.append(decode_escape(c, stm))
        elif c == '"':
            return ''.join(r)
        elif c > '\x7f':
            r.append(_decode_utf8(c, stm))
        else:
            r.append(c)


def _from_json_fixed(stm, expected, value, errmsg):
    off = len(expected)
    pos = stm.pos
    if stm.substr(pos, off) == expected:
        next(stm, off)
        return value
    raise JSONError(errmsg, stm, pos)


def _from_json_number(stm):
    is_float = 0
    saw_exp = 0
    pos = stm.pos
    while True:
        c = stm.peek()
        if c not in NUMCHARS:
            break
        elif c == '-' and not saw_exp:
            pass
        elif c in('.', 'e', 'E'):
            is_float = 1
            if c in('e', 'E'):
                saw_exp = 1
        next(stm)
    s = stm.substr(pos, stm.pos-pos)
    if is_float:
        return float(s)
    return int(s)


def _from_json_list(stm):
    next(stm)
    result = []
    pos = stm.pos
    while True:
        stm.skipspaces()
        c = stm.peek()
        if c == '':
            raise JSONError(E_TRUNC, stm, pos)
        elif c == ']':
            next(stm)
            return result
        elif c == ',':
            next(stm)
            result.append(_from_json_raw(stm))
            continue
        elif not result:
            result.append(_from_json_raw(stm))
            continue
        else:
            raise JSONError(E_MALF, stm, stm.pos)


def _from_json_dict(stm):
    next(stm)
    result = {}
    expect_key = 0
    pos = stm.pos
    while True:
        stm.skipspaces()
        c = stm.peek()
        if c == '':
            raise JSONError(E_TRUNC, stm, pos)
        if expect_key and c in('}', ','):
            raise JSONError(E_DKEY, stm, stm.pos)
        if c in('}', ','):
            next(stm)
            if c == '}':
                return result
            expect_key = 1
            continue
        elif c == '"':
            key = _from_json_string(stm)
            stm.skipspaces()
            c = next(stm)
            if c != ':':
                raise JSONError(E_COLON, stm, stm.pos)
            stm.skipspaces()
            val = _from_json_raw(stm)
            result[key] = val
            expect_key = 0
            continue
        raise JSONError(E_MALF, stm, stm.pos)


def _from_json_raw(stm):
    while True:
        stm.skipspaces()
        c = stm.peek()
        if c == '"':
            return _from_json_string(stm)
        elif c == '{':
            return _from_json_dict(stm)
        elif c == '[':
            return _from_json_list(stm)
        elif c == 't':
            return _from_json_fixed(stm, 'true', True, E_BOOL)
        elif c == 'f':
            return _from_json_fixed(stm, 'false', False, E_BOOL)
        elif c == 'n':
            return _from_json_fixed(stm, 'null', None, E_NULL)
        elif c in NUMSTART:
            return _from_json_number(stm)
        raise JSONError(E_MALF, stm, stm.pos)


def from_json(data):
    if not isinstance(data, str):
        raise JSONError(E_BYTES)
    if not data:
        return None
    stm = JSONStream(data)
    return _from_json_raw(stm)


decode = from_json

# std
import sys
import unittest

class TestMicrojsonParse(unittest.TestCase):

    def _run_cases(self, cases):
        for js, py in cases:
            r = from_json(js)
            self.assertEqual(r, py)

    def test_dict(self):
        T_PARSE_DICTS = [
        ('{}', {}),
        ('{"a":1}', {"a":1}),
        ('{"abcdef": "ghijkl"}', {'abcdef': 'ghijkl'}),

        # whitespace tests
        ('\t{\n\r\t }\r\n', {}),
        (' \t{ "a"\n:\t"b"\n\t}  ', {"a":"b"})
        ]
        self._run_cases(T_PARSE_DICTS)

    def test_list(self):
        T_PARSE_LISTS = [
        ('[]', []),
        ('[1,2,3]', [1,2,3]),
        ('[[1,2],["a","b"]]', [[1,2],["a","b"]]),

        # whitespace tests
        ('\t\n[\r\n \t]\n', []),
        ('  [\n\t1,\t2 ] \t', [1,2])

        ]
        self._run_cases(T_PARSE_LISTS)

    def test_string(self):
        T_PARSE_STRS = [
            ('', None),

            ('"foo bar baz"', 'foo bar baz'),
            ('"abc\\"def\\"ghi"', 'abc"def"ghi'),

            # escaped whitespace
            ('"\\n\\tindent\\r\\n"', '\n\tindent\r\n'),

            # escaped ascii, weird but need to test to cover possible cases
            ('"\\ \\x\\y\\z\\ "', ' xyz '),

            # escaped unicode 
            #('"\u0124\u0113\u013a\u013e\u014d"', u"\u0124\u0113\u013a\u013e\u014d"),
            #('"\u201chello\u201d"', u"\u201chello\u201d"),

            # bare utf-8 
            ('"\xc6\x91"', u"\u0191"),
            ('"\xc4\x91"', u"\u0111"),

            # mixed utf-8 and escaped unicode
            #('"a\xc6\x91b\u0191c\u2018"', u"a\u0191b\u0191c\u2018"),
            ]

        # utf-8 encoded ucs-4 test case
        if sys.maxunicode == 1114111:
            T_PARSE_STRS += [
                # pure utf-8 char > 16-bits. not asci-encodable in json.
                ('"\xf0\x90\x82\x82"', U"\U00010082")
            ]
        self._run_cases(T_PARSE_STRS)

    def test_integer(self):
        T_PARSE_INTS = [
        ('0', 0),
        ('-1', -1),
        ('123', 123), 
        ('-2147483648', -2147483648),
        ('2147483648', 2147483648),
        ('4294967296', 4294967296),
        ('9223372036854775808', 9223372036854775808),
        ('18446744073709551616', 18446744073709551616)
        ]
        self._run_cases(T_PARSE_INTS)
    
    def test_floats(self):
        T_PARSE_FLOATS = [
        ('.1', 0.1),
        ('-.1', -0.1),
        ('1.0', 1.0),
        ('-1.0', -1.0),
        ('3.14159', 3.14159),
        ('-3.14159', -3.14159),
        ('1E1', 1E1),
        ('-1E2', -1E2),
        ('-1E-2', -1E-2),
        ('12E-2', 12E-2),
        ('1.8446744073709552e19', 1.8446744073709552e19)
        ]
        self._run_cases(T_PARSE_FLOATS)

    def test_null_and_bool(self):
        T_PARSE_FIXED = [('true', True), ('false', False), ('null', None)]
        self._run_cases(T_PARSE_FIXED)

    def test_malformed(self):
        "assert a JSONError is raised for these cases"
        T_PARSE_MALFORMED = [
        'wegouhweg',    # naked char data
        '["abcdef]',    # string missing trailing '"'
        '["a","b"',     # list missing trailing ']'
        '{"a:"b"}',     # key missing trailing '"'
        '{"a":13',      # dict missing trailing '}'
        '{123: 456}',   # object keys must be quoted
        '[nulx]',       # null?
        '[trux]',       # true?
        "[12, ]",       # incomplete list
        "[123",         # truncated list
        "[1, , ,]",     # list with empty slots
        "[1, , ",       # truncated list with empty slots
        "[#",           # list with illegal chars
        "[1, 2\n#",     # list with illegal chars
        '{"abc"}',      # incomplete dict
        '{"abc"',       # truncated dict
        '{"abc":',      # truncated dict with missing value
        '{',            # truncated dict
        '{,}',          # dict with empty slots
        #u'[]',          # input must be a str
        #'{"a":1"b":2}'  # missing comma
        ]
        for js in T_PARSE_MALFORMED:
            self.assertRaises(JSONError, from_json, js)

def main(s):
    result = from_json(s)
    return result

if __name__ == "__main__":
    main(sys.argv[1])