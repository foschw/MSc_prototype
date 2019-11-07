#from __future__ import absolute_import
#__version__ = '3.16.1'
__all__ = [
    'dump', 'dumps', 'load', 'loads',
    'JSONDecoder', 'JSONDecodeError', 'JSONEncoder',
    'OrderedDict', 'simple_first', 'RawJSON', 'text_type', 'long_type', 'PosInf', 'NegInf', 'NaN'
    'decoder', 'encoder', 'reload_module'
]

#__author__ = 'Bob Ippolito <bob@redivi.com>'

from decimal import Decimal

#from .errors import JSONDecodeError
def linecol(doc, pos):
    lineno = doc.count('\n', 0, pos) + 1
    if lineno == 1:
        colno = pos + 1
    else:
        colno = pos - doc.rindex('\n', 0, pos)
    return lineno, colno


def errmsg(msg, doc, pos, end=None):
    lineno, colno = linecol(doc, pos)
    msg = msg.replace('%r', repr(doc[pos:pos + 1]))
    if end is None:
        fmt = '%s: line %d column %d (char %d)'
        return fmt % (msg, lineno, colno, pos)
    endlineno, endcolno = linecol(doc, end)
    fmt = '%s: line %d column %d - line %d column %d (char %d - %d)'
    return fmt % (msg, lineno, colno, endlineno, endcolno, pos, end)


class JSONDecodeError(ValueError):
    """Subclass of ValueError with the following additional properties:

    msg: The unformatted error message
    doc: The JSON document being parsed
    pos: The start index of doc where parsing failed
    end: The end index of doc where parsing failed (may be None)
    lineno: The line corresponding to pos
    colno: The column corresponding to pos
    endlineno: The line corresponding to end (may be None)
    endcolno: The column corresponding to end (may be None)

    """
    # Note that this exception is used from _speedups
    def __init__(self, msg, doc, pos, end=None):
        ValueError.__init__(self, errmsg(msg, doc, pos, end=end))
        self.msg = msg
        self.doc = doc
        self.pos = pos
        self.end = end
        self.lineno, self.colno = linecol(doc, pos)
        if end is not None:
            self.endlineno, self.endcolno = linecol(doc, end)
        else:
            self.endlineno, self.endcolno = None, None

    def __reduce__(self):
        return self.__class__, (self.msg, self.doc, self.pos, self.end)
#from .errors import JSONDecodeError
#from .raw_json import RawJSON
class RawJSON(object):
    """Wrap an encoded JSON document for direct embedding in the output

    """
    def __init__(self, encoded_json):
        self.encoded_json = encoded_json
#from .raw_json import RawJSON
#from .decoder import JSONDecoder

import re
import sys
import struct
#from .compat import PY3
"""Python 3 compatibility shims
"""
import sys
PY3 = True
if sys.version_info[:2] >= (3, 4):
    from importlib import reload as reload_module
else:
    from imp import reload as reload_module
def b(s):
    return bytes(s, 'latin1')
from io import StringIO, BytesIO
text_type = str
binary_type = bytes
string_types = (str,)
integer_types = (int,)
unichr = chr

long_type = integer_types[-1]
#from .compat import PY3
#from .scanner import make_scanner, JSONDecodeError
"""JSON token scanner
"""
import re
#from .errors import JSONDecodeError
__all__ = ['make_scanner', 'JSONDecodeError']

NUMBER_RE = re.compile(
    r'(-?(?:0|[1-9]\d*))(\.\d+)?([eE][-+]?\d+)?',
    (re.VERBOSE | re.MULTILINE | re.DOTALL))


def py_make_scanner(context):
    parse_object = context.parse_object
    parse_array = context.parse_array
    parse_string = context.parse_string
    match_number = NUMBER_RE.match
    encoding = context.encoding
    strict = context.strict
    parse_float = context.parse_float
    parse_int = context.parse_int
    parse_constant = context.parse_constant
    object_hook = context.object_hook
    object_pairs_hook = context.object_pairs_hook
    memo = context.memo

    def _scan_once(string, idx):
        errmsg = 'Expecting value'
        try:
            nextchar = string[idx]
        except IndexError:
            raise JSONDecodeError(errmsg, string, idx)

        if nextchar == '"':
            return parse_string(string, idx + 1, encoding, strict)
        elif nextchar == '{':
            return parse_object((string, idx + 1), encoding, strict,
                _scan_once, object_hook, object_pairs_hook, memo)
        elif nextchar == '[':
            return parse_array((string, idx + 1), _scan_once)
        elif nextchar == 'n' and string[idx:idx + 4] == 'null':
            return None, idx + 4
        elif nextchar == 't' and string[idx:idx + 4] == 'true':
            return True, idx + 4
        elif nextchar == 'f' and string[idx:idx + 5] == 'false':
            return False, idx + 5

        m = match_number(string, idx)
        if m is not None:
            integer, frac, exp = m.groups()
            if frac or exp:
                res = parse_float(integer + (frac or '') + (exp or ''))
            else:
                res = parse_int(integer)
            return res, m.end()
        elif nextchar == 'N' and string[idx:idx + 3] == 'NaN':
            return parse_constant('NaN'), idx + 3
        elif nextchar == 'I' and string[idx:idx + 8] == 'Infinity':
            return parse_constant('Infinity'), idx + 8
        elif nextchar == '-' and string[idx:idx + 9] == '-Infinity':
            return parse_constant('-Infinity'), idx + 9
        else:
            raise JSONDecodeError(errmsg, string, idx)

    def scan_once(string, idx):
        if idx < 0:
            # Ensure the same behavior as the C speedup, otherwise
            # this would work for *some* negative string indices due
            # to the behavior of __getitem__ for strings. #98
            raise JSONDecodeError('Expecting value', string, idx)
        try:
            return _scan_once(string, idx)
        finally:
            memo.clear()

    return scan_once

make_scanner = py_make_scanner
#from .scanner import make_scanner, JSONDecodeError

# NOTE (3.1.0): JSONDecodeError may still be imported from this module for
# compatibility, but it was never in the __all__
__all__ = ['JSONDecoder']

FLAGS = re.VERBOSE | re.MULTILINE | re.DOTALL

def _floatconstants():
    if sys.version_info < (2, 6):
        _BYTES = '7FF80000000000007FF0000000000000'.decode('hex')
        nan, inf = struct.unpack('>dd', _BYTES)
    else:
        nan = float('nan')
        inf = float('inf')
    return nan, inf, -inf

NaN, PosInf, NegInf = _floatconstants()

_CONSTANTS = {
    '-Infinity': NegInf,
    'Infinity': PosInf,
    'NaN': NaN,
}

STRINGCHUNK = re.compile(r'(.*?)(["\\\x00-\x1f])', FLAGS)
BACKSLASH = {
    '"': u'"', '\\': u'\\', '/': u'/',
    'b': u'\b', 'f': u'\f', 'n': u'\n', 'r': u'\r', 't': u'\t',
}

DEFAULT_ENCODING = "utf-8"

def py_scanstring(s, end, encoding=None, strict=True,
        _b=BACKSLASH, _m=STRINGCHUNK.match, _join=u''.join,
        _PY3=PY3, _maxunicode=sys.maxunicode):
    """Scan the string s for a JSON string. End is the index of the
    character in s after the quote that started the JSON string.
    Unescapes all valid JSON string escape sequences and raises ValueError
    on attempt to decode an invalid string. If strict is False then literal
    control characters are allowed in the string.

    Returns a tuple of the decoded string and the index of the character in s
    after the end quote."""
    if encoding is None:
        encoding = DEFAULT_ENCODING
    chunks = []
    _append = chunks.append
    begin = end - 1
    while 1:
        chunk = _m(s, end)
        if chunk is None:
            raise JSONDecodeError(
                "Unterminated string starting at", s, begin)
        end = chunk.end()
        content, terminator = chunk.groups()
        # Content is contains zero or more unescaped string characters
        if content:
            if not _PY3 and not isinstance(content, unicode):
                content = unicode(content, encoding)
            _append(content)
        # Terminator is the end of string, a literal control character,
        # or a backslash denoting that an escape sequence follows
        if terminator == '"':
            break
        elif terminator != '\\':
            if strict:
                msg = "Invalid control character %r at"
                raise JSONDecodeError(msg, s, end)
            else:
                _append(terminator)
                continue
        try:
            esc = s[end]
        except IndexError:
            raise JSONDecodeError(
                "Unterminated string starting at", s, begin)
        # If not a unicode escape sequence, must be in the lookup table
        if esc != 'u':
            try:
                char = _b[esc]
            except KeyError:
                msg = "Invalid \\X escape sequence %r"
                raise JSONDecodeError(msg, s, end)
            end += 1
        else:
            # Unicode escape sequence
            msg = "Invalid \\uXXXX escape sequence"
            esc = s[end + 1:end + 5]
            escX = esc[1:2]
            if len(esc) != 4 or escX == 'x' or escX == 'X':
                raise JSONDecodeError(msg, s, end - 1)
            try:
                uni = int(esc, 16)
            except ValueError:
                raise JSONDecodeError(msg, s, end - 1)
            end += 5
            # Check for surrogate pair on UCS-4 systems
            # Note that this will join high/low surrogate pairs
            # but will also pass unpaired surrogates through
            if (_maxunicode > 65535 and
                uni & 0xfc00 == 0xd800 and
                s[end:end + 2] == '\\u'):
                esc2 = s[end + 2:end + 6]
                escX = esc2[1:2]
                if len(esc2) == 4 and not (escX == 'x' or escX == 'X'):
                    try:
                        uni2 = int(esc2, 16)
                    except ValueError:
                        raise JSONDecodeError(msg, s, end)
                    if uni2 & 0xfc00 == 0xdc00:
                        uni = 0x10000 + (((uni - 0xd800) << 10) |
                                         (uni2 - 0xdc00))
                        end += 6
            char = chr(uni)
        # Append the unescaped character
        _append(char)
    return _join(chunks), end


# Use speedup if available
scanstring = py_scanstring

WHITESPACE = re.compile(r'[ \t\n\r]*', FLAGS)
WHITESPACE_STR = ' \t\n\r'

def JSONObject(state, encoding, strict, scan_once, object_hook,
        object_pairs_hook, memo=None,
        _w=WHITESPACE.match, _ws=WHITESPACE_STR):
    (s, end) = state
    # Backwards compatibility
    if memo is None:
        memo = {}
    memo_get = memo.setdefault
    pairs = []
    # Use a slice to prevent IndexError from being raised, the following
    # check will raise a more specific ValueError if the string is empty
    nextchar = s[end:end + 1]
    # Normally we expect nextchar == '"'
    if nextchar != '"':
        if nextchar in _ws:
            end = _w(s, end).end()
            nextchar = s[end:end + 1]
        # Trivial empty object
        if nextchar == '}':
            if object_pairs_hook is not None:
                result = object_pairs_hook(pairs)
                return result, end + 1
            pairs = {}
            if object_hook is not None:
                pairs = object_hook(pairs)
            return pairs, end + 1
        elif nextchar != '"':
            raise JSONDecodeError(
                "Expecting property name enclosed in double quotes",
                s, end)
    end += 1
    while True:
        key, end = scanstring(s, end, encoding, strict)
        key = memo_get(key, key)

        # To skip some function call overhead we optimize the fast paths where
        # the JSON key separator is ": " or just ":".
        if s[end:end + 1] != ':':
            end = _w(s, end).end()
            if s[end:end + 1] != ':':
                raise JSONDecodeError("Expecting ':' delimiter", s, end)

        end += 1

        try:
            if s[end] in _ws:
                end += 1
                if s[end] in _ws:
                    end = _w(s, end + 1).end()
        except IndexError:
            pass

        value, end = scan_once(s, end)
        pairs.append((key, value))

        try:
            nextchar = s[end]
            if nextchar in _ws:
                end = _w(s, end + 1).end()
                nextchar = s[end]
        except IndexError:
            nextchar = ''
        end += 1

        if nextchar == '}':
            break
        elif nextchar != ',':
            raise JSONDecodeError("Expecting ',' delimiter or '}'", s, end - 1)

        try:
            nextchar = s[end]
            if nextchar in _ws:
                end += 1
                nextchar = s[end]
                if nextchar in _ws:
                    end = _w(s, end + 1).end()
                    nextchar = s[end]
        except IndexError:
            nextchar = ''

        end += 1
        if nextchar != '"':
            raise JSONDecodeError(
                "Expecting property name enclosed in double quotes",
                s, end - 1)

    if object_pairs_hook is not None:
        result = object_pairs_hook(pairs)
        return result, end
    pairs = dict(pairs)
    if object_hook is not None:
        pairs = object_hook(pairs)
    return pairs, end

def JSONArray(state, scan_once, _w=WHITESPACE.match, _ws=WHITESPACE_STR):
    (s, end) = state
    values = []
    nextchar = s[end:end + 1]
    if nextchar in _ws:
        end = _w(s, end + 1).end()
        nextchar = s[end:end + 1]
    # Look-ahead for trivial empty array
    if nextchar == ']':
        return values, end + 1
    elif nextchar == '':
        raise JSONDecodeError("Expecting value or ']'", s, end)
    _append = values.append
    while True:
        value, end = scan_once(s, end)
        _append(value)
        nextchar = s[end:end + 1]
        if nextchar in _ws:
            end = _w(s, end + 1).end()
            nextchar = s[end:end + 1]
        end += 1
        if nextchar == ']':
            break
        elif nextchar != ',':
            raise JSONDecodeError("Expecting ',' delimiter or ']'", s, end - 1)

        try:
            if s[end] in _ws:
                end += 1
                if s[end] in _ws:
                    end = _w(s, end + 1).end()
        except IndexError:
            pass

    return values, end

class JSONDecoder(object):
    """Simple JSON <http://json.org> decoder

    Performs the following translations in decoding by default:

    +---------------+-------------------+
    | JSON          | Python            |
    +===============+===================+
    | object        | dict              |
    +---------------+-------------------+
    | array         | list              |
    +---------------+-------------------+
    | string        | str, unicode      |
    +---------------+-------------------+
    | number (int)  | int, long         |
    +---------------+-------------------+
    | number (real) | float             |
    +---------------+-------------------+
    | true          | True              |
    +---------------+-------------------+
    | false         | False             |
    +---------------+-------------------+
    | null          | None              |
    +---------------+-------------------+

    It also understands ``NaN``, ``Infinity``, and ``-Infinity`` as
    their corresponding ``float`` values, which is outside the JSON spec.

    """

    def __init__(self, encoding=None, object_hook=None, parse_float=None,
            parse_int=None, parse_constant=None, strict=True,
            object_pairs_hook=None):
        """
        *encoding* determines the encoding used to interpret any
        :class:`str` objects decoded by this instance (``'utf-8'`` by
        default).  It has no effect when decoding :class:`unicode` objects.

        Note that currently only encodings that are a superset of ASCII work,
        strings of other encodings should be passed in as :class:`unicode`.

        *object_hook*, if specified, will be called with the result of every
        JSON object decoded and its return value will be used in place of the
        given :class:`dict`.  This can be used to provide custom
        deserializations (e.g. to support JSON-RPC class hinting).

        *object_pairs_hook* is an optional function that will be called with
        the result of any object literal decode with an ordered list of pairs.
        The return value of *object_pairs_hook* will be used instead of the
        :class:`dict`.  This feature can be used to implement custom decoders
        that rely on the order that the key and value pairs are decoded (for
        example, :func:`collections.OrderedDict` will remember the order of
        insertion). If *object_hook* is also defined, the *object_pairs_hook*
        takes priority.

        *parse_float*, if specified, will be called with the string of every
        JSON float to be decoded.  By default, this is equivalent to
        ``float(num_str)``. This can be used to use another datatype or parser
        for JSON floats (e.g. :class:`decimal.Decimal`).

        *parse_int*, if specified, will be called with the string of every
        JSON int to be decoded.  By default, this is equivalent to
        ``int(num_str)``.  This can be used to use another datatype or parser
        for JSON integers (e.g. :class:`float`).

        *parse_constant*, if specified, will be called with one of the
        following strings: ``'-Infinity'``, ``'Infinity'``, ``'NaN'``.  This
        can be used to raise an exception if invalid JSON numbers are
        encountered.

        *strict* controls the parser's behavior when it encounters an
        invalid control character in a string. The default setting of
        ``True`` means that unescaped control characters are parse errors, if
        ``False`` then control characters will be allowed in strings.

        """
        if encoding is None:
            encoding = DEFAULT_ENCODING
        self.encoding = encoding
        self.object_hook = object_hook
        self.object_pairs_hook = object_pairs_hook
        self.parse_float = parse_float or float
        self.parse_int = parse_int or int
        self.parse_constant = parse_constant or _CONSTANTS.__getitem__
        self.strict = strict
        self.parse_object = JSONObject
        self.parse_array = JSONArray
        self.parse_string = scanstring
        self.memo = {}
        self.scan_once = make_scanner(self)

    def decode(self, s, _w=WHITESPACE.match, _PY3=PY3):
        """Return the Python representation of ``s`` (a ``str`` or ``unicode``
        instance containing a JSON document)

        """
        if _PY3 and isinstance(s, bytes):
            s = str(s, self.encoding)
        obj, end = self.raw_decode(s)
        end = _w(s, end).end()
        if end != len(s):
            raise JSONDecodeError("Extra data", s, end, len(s))
        return obj

    def raw_decode(self, s, idx=0, _w=WHITESPACE.match, _PY3=PY3):
        """Decode a JSON document from ``s`` (a ``str`` or ``unicode``
        beginning with a JSON document) and return a 2-tuple of the Python
        representation and the index in ``s`` where the document ended.
        Optionally, ``idx`` can be used to specify an offset in ``s`` where
        the JSON document begins.

        This can be used to decode a JSON document from a string that may
        have extraneous data at the end.

        """
        if idx < 0:
            # Ensure that raw_decode bails on negative indexes, the regex
            # would otherwise mask this behavior. #98
            raise JSONDecodeError('Expecting value', s, idx)
        if _PY3 and not isinstance(s, str):
            raise TypeError("Input string must be text, not bytes")
        # strip UTF-8 bom
        if len(s) > idx:
            ord0 = ord(s[idx])
            if ord0 == 0xfeff:
                idx += 1
            elif ord0 == 0xef and s[idx:idx + 3] == '\xef\xbb\xbf':
                idx += 3
        return self.scan_once(s, idx=_w(s, idx).end())
#from .decoder import JSONDecoder
#from .encoder import JSONEncoder, JSONEncoderForHTML
"""Implementation of JSONEncoder
"""
import re
from operator import itemgetter
# Do not import Decimal directly to avoid reload issues
import decimal
#from .compat import unichr, binary_type, text_type, string_types, integer_types, PY3

#from .decoder import PosInf
#from .raw_json import RawJSON

ESCAPE = re.compile(r'[\x00-\x1f\\"]')
ESCAPE_ASCII = re.compile(r'([\\"]|[^\ -~])')
HAS_UTF8 = re.compile(r'[\x80-\xff]')
ESCAPE_DCT = {
    '\\': '\\\\',
    '"': '\\"',
    '\b': '\\b',
    '\f': '\\f',
    '\n': '\\n',
    '\r': '\\r',
    '\t': '\\t',
}
for i in range(0x20):
    #ESCAPE_DCT.setdefault(chr(i), '\\u{0:04x}'.format(i))
    ESCAPE_DCT.setdefault(chr(i), '\\u%04x' % (i,))

FLOAT_REPR = repr

def encode_basestring(s, _PY3=PY3, _q=u'"'):
    """Return a JSON representation of a Python string

    """
    if _PY3:
        if isinstance(s, bytes):
            s = str(s, 'utf-8')
        elif type(s) is not str:
            # convert an str subclass instance to exact str
            # raise a TypeError otherwise
            s = str.__str__(s)
    else:
        if isinstance(s, str) and HAS_UTF8.search(s) is not None:
            s = unicode(s, 'utf-8')
        elif type(s) not in (str, unicode):
            # convert an str subclass instance to exact str
            # convert a unicode subclass instance to exact unicode
            # raise a TypeError otherwise
            if isinstance(s, str):
                s = str.__str__(s)
            else:
                s = unicode.__getnewargs__(s)[0]
    def replace(match):
        return ESCAPE_DCT[match.group(0)]
    return _q + ESCAPE.sub(replace, s) + _q


def py_encode_basestring_ascii(s, _PY3=PY3):
    """Return an ASCII-only JSON representation of a Python string

    """
    if _PY3:
        if isinstance(s, bytes):
            s = str(s, 'utf-8')
        elif type(s) is not str:
            # convert an str subclass instance to exact str
            # raise a TypeError otherwise
            s = str.__str__(s)
    else:
        if isinstance(s, str) and HAS_UTF8.search(s) is not None:
            s = unicode(s, 'utf-8')
        elif type(s) not in (str, unicode):
            # convert an str subclass instance to exact str
            # convert a unicode subclass instance to exact unicode
            # raise a TypeError otherwise
            if isinstance(s, str):
                s = str.__str__(s)
            else:
                s = unicode.__getnewargs__(s)[0]
    def replace(match):
        s = match.group(0)
        try:
            return ESCAPE_DCT[s]
        except KeyError:
            n = ord(s)
            if n < 0x10000:
                #return '\\u{0:04x}'.format(n)
                return '\\u%04x' % (n,)
            else:
                # surrogate pair
                n -= 0x10000
                s1 = 0xd800 | ((n >> 10) & 0x3ff)
                s2 = 0xdc00 | (n & 0x3ff)
                #return '\\u{0:04x}\\u{1:04x}'.format(s1, s2)
                return '\\u%04x\\u%04x' % (s1, s2)
    return '"' + str(ESCAPE_ASCII.sub(replace, s)) + '"'


encode_basestring_ascii = (
    py_encode_basestring_ascii)

class JSONEncoder(object):
    """Extensible JSON <http://json.org> encoder for Python data structures.

    Supports the following objects and types by default:

    +-------------------+---------------+
    | Python            | JSON          |
    +===================+===============+
    | dict, namedtuple  | object        |
    +-------------------+---------------+
    | list, tuple       | array         |
    +-------------------+---------------+
    | str, unicode      | string        |
    +-------------------+---------------+
    | int, long, float  | number        |
    +-------------------+---------------+
    | True              | true          |
    +-------------------+---------------+
    | False             | false         |
    +-------------------+---------------+
    | None              | null          |
    +-------------------+---------------+

    To extend this to recognize other objects, subclass and implement a
    ``.default()`` method with another method that returns a serializable
    object for ``o`` if possible, otherwise it should call the superclass
    implementation (to raise ``TypeError``).

    """
    item_separator = ', '
    key_separator = ': '

    def __init__(self, skipkeys=False, ensure_ascii=True,
                 check_circular=True, allow_nan=True, sort_keys=False,
                 indent=None, separators=None, encoding='utf-8', default=None,
                 use_decimal=True, namedtuple_as_object=True,
                 tuple_as_array=True, bigint_as_string=False,
                 item_sort_key=None, for_json=False, ignore_nan=False,
                 int_as_string_bitcount=None, iterable_as_array=False):
        """Constructor for JSONEncoder, with sensible defaults.

        If skipkeys is false, then it is a TypeError to attempt
        encoding of keys that are not str, int, long, float or None.  If
        skipkeys is True, such items are simply skipped.

        If ensure_ascii is true, the output is guaranteed to be str
        objects with all incoming unicode characters escaped.  If
        ensure_ascii is false, the output will be unicode object.

        If check_circular is true, then lists, dicts, and custom encoded
        objects will be checked for circular references during encoding to
        prevent an infinite recursion (which would cause an OverflowError).
        Otherwise, no such check takes place.

        If allow_nan is true, then NaN, Infinity, and -Infinity will be
        encoded as such.  This behavior is not JSON specification compliant,
        but is consistent with most JavaScript based encoders and decoders.
        Otherwise, it will be a ValueError to encode such floats.

        If sort_keys is true, then the output of dictionaries will be
        sorted by key; this is useful for regression tests to ensure
        that JSON serializations can be compared on a day-to-day basis.

        If indent is a string, then JSON array elements and object members
        will be pretty-printed with a newline followed by that string repeated
        for each level of nesting. ``None`` (the default) selects the most compact
        representation without any newlines. For backwards compatibility with
        versions of simplejson earlier than 2.1.0, an integer is also accepted
        and is converted to a string with that many spaces.

        If specified, separators should be an (item_separator, key_separator)
        tuple.  The default is (', ', ': ') if *indent* is ``None`` and
        (',', ': ') otherwise.  To get the most compact JSON representation,
        you should specify (',', ':') to eliminate whitespace.

        If specified, default is a function that gets called for objects
        that can't otherwise be serialized.  It should return a JSON encodable
        version of the object or raise a ``TypeError``.

        If encoding is not None, then all input strings will be
        transformed into unicode using that encoding prior to JSON-encoding.
        The default is UTF-8.

        If use_decimal is true (default: ``True``), ``decimal.Decimal`` will
        be supported directly by the encoder. For the inverse, decode JSON
        with ``parse_float=decimal.Decimal``.

        If namedtuple_as_object is true (the default), objects with
        ``_asdict()`` methods will be encoded as JSON objects.

        If tuple_as_array is true (the default), tuple (and subclasses) will
        be encoded as JSON arrays.

        If *iterable_as_array* is true (default: ``False``),
        any object not in the above table that implements ``__iter__()``
        will be encoded as a JSON array.

        If bigint_as_string is true (not the default), ints 2**53 and higher
        or lower than -2**53 will be encoded as strings. This is to avoid the
        rounding that happens in Javascript otherwise.

        If int_as_string_bitcount is a positive number (n), then int of size
        greater than or equal to 2**n or lower than or equal to -2**n will be
        encoded as strings.

        If specified, item_sort_key is a callable used to sort the items in
        each dictionary. This is useful if you want to sort items other than
        in alphabetical order by key.

        If for_json is true (not the default), objects with a ``for_json()``
        method will use the return value of that method for encoding as JSON
        instead of the object.

        If *ignore_nan* is true (default: ``False``), then out of range
        :class:`float` values (``nan``, ``inf``, ``-inf``) will be serialized
        as ``null`` in compliance with the ECMA-262 specification. If true,
        this will override *allow_nan*.

        """

        self.skipkeys = skipkeys
        self.ensure_ascii = ensure_ascii
        self.check_circular = check_circular
        self.allow_nan = allow_nan
        self.sort_keys = sort_keys
        self.use_decimal = use_decimal
        self.namedtuple_as_object = namedtuple_as_object
        self.tuple_as_array = tuple_as_array
        self.iterable_as_array = iterable_as_array
        self.bigint_as_string = bigint_as_string
        self.item_sort_key = item_sort_key
        self.for_json = for_json
        self.ignore_nan = ignore_nan
        self.int_as_string_bitcount = int_as_string_bitcount
        if indent is not None and not isinstance(indent, string_types):
            indent = indent * ' '
        self.indent = indent
        if separators is not None:
            self.item_separator, self.key_separator = separators
        elif indent is not None:
            self.item_separator = ','
        if default is not None:
            self.default = default
        self.encoding = encoding

    def default(self, o):
        """Implement this method in a subclass such that it returns
        a serializable object for ``o``, or calls the base implementation
        (to raise a ``TypeError``).

        For example, to support arbitrary iterators, you could
        implement default like this::

            def default(self, o):
                try:
                    iterable = iter(o)
                except TypeError:
                    pass
                else:
                    return list(iterable)
                return JSONEncoder.default(self, o)

        """
        raise TypeError('Object of type %s is not JSON serializable' %
                        o.__class__.__name__)

    def encode(self, o):
        """Return a JSON string representation of a Python data structure.

        >>> from simplejson import JSONEncoder
        >>> JSONEncoder().encode({"foo": ["bar", "baz"]})
        '{"foo": ["bar", "baz"]}'

        """
        # This is for extremely simple cases and benchmarks.
        if isinstance(o, binary_type):
            _encoding = self.encoding
            if (_encoding is not None and not (_encoding == 'utf-8')):
                o = text_type(o, _encoding)
        if isinstance(o, string_types):
            if self.ensure_ascii:
                return encode_basestring_ascii(o)
            else:
                return encode_basestring(o)
        # This doesn't pass the iterator directly to ''.join() because the
        # exceptions aren't as detailed.  The list call should be roughly
        # equivalent to the PySequence_Fast that ''.join() would do.
        chunks = self.iterencode(o, _one_shot=True)
        if not isinstance(chunks, (list, tuple)):
            chunks = list(chunks)
        if self.ensure_ascii:
            return ''.join(chunks)
        else:
            return u''.join(chunks)

    def iterencode(self, o, _one_shot=False):
        """Encode the given object and yield each string
        representation as available.

        For example::

            for chunk in JSONEncoder().iterencode(bigobject):
                mysocket.write(chunk)

        """
        if self.check_circular:
            markers = {}
        else:
            markers = None
        if self.ensure_ascii:
            _encoder = encode_basestring_ascii
        else:
            _encoder = encode_basestring
        if self.encoding != 'utf-8' and self.encoding is not None:
            def _encoder(o, _orig_encoder=_encoder, _encoding=self.encoding):
                if isinstance(o, binary_type):
                    o = text_type(o, _encoding)
                return _orig_encoder(o)

        def floatstr(o, allow_nan=self.allow_nan, ignore_nan=self.ignore_nan,
                _repr=FLOAT_REPR, _inf=PosInf, _neginf=-PosInf):
            # Check for specials. Note that this type of test is processor
            # and/or platform-specific, so do tests which don't depend on
            # the internals.

            if o != o:
                text = 'NaN'
            elif o == _inf:
                text = 'Infinity'
            elif o == _neginf:
                text = '-Infinity'
            else:
                if type(o) != float:
                    # See #118, do not trust custom str/repr
                    o = float(o)
                return _repr(o)

            if ignore_nan:
                text = 'null'
            elif not allow_nan:
                raise ValueError(
                    "Out of range float values are not JSON compliant: " +
                    repr(o))

            return text

        key_memo = {}
        int_as_string_bitcount = (
            53 if self.bigint_as_string else self.int_as_string_bitcount)
        _iterencode = _make_iterencode(
                markers, self.default, _encoder, self.indent, floatstr,
                self.key_separator, self.item_separator, self.sort_keys,
                self.skipkeys, _one_shot, self.use_decimal,
                self.namedtuple_as_object, self.tuple_as_array,
                int_as_string_bitcount,
                self.item_sort_key, self.encoding, self.for_json,
                self.iterable_as_array, Decimal=decimal.Decimal)
        try:
            return _iterencode(o, 0)
        finally:
            key_memo.clear()


class JSONEncoderForHTML(JSONEncoder):
    """An encoder that produces JSON safe to embed in HTML.

    To embed JSON content in, say, a script tag on a web page, the
    characters &, < and > should be escaped. They cannot be escaped
    with the usual entities (e.g. &amp;) because they are not expanded
    within <script> tags.

    This class also escapes the line separator and paragraph separator
    characters U+2028 and U+2029, irrespective of the ensure_ascii setting,
    as these characters are not valid in JavaScript strings (see
    http://timelessrepo.com/json-isnt-a-javascript-subset).
    """

    def encode(self, o):
        # Override JSONEncoder.encode because it has hacks for
        # performance that make things more complicated.
        chunks = self.iterencode(o, True)
        if self.ensure_ascii:
            return ''.join(chunks)
        else:
            return u''.join(chunks)

    def iterencode(self, o, _one_shot=False):
        chunks = super(JSONEncoderForHTML, self).iterencode(o, _one_shot)
        for chunk in chunks:
            chunk = chunk.replace('&', '\\u0026')
            chunk = chunk.replace('<', '\\u003c')
            chunk = chunk.replace('>', '\\u003e')

            if not self.ensure_ascii:
                chunk = chunk.replace(u'\u2028', '\\u2028')
                chunk = chunk.replace(u'\u2029', '\\u2029')

            yield chunk


def _make_iterencode(markers, _default, _encoder, _indent, _floatstr,
        _key_separator, _item_separator, _sort_keys, _skipkeys, _one_shot,
        _use_decimal, _namedtuple_as_object, _tuple_as_array,
        _int_as_string_bitcount, _item_sort_key,
        _encoding,_for_json,
        _iterable_as_array,
        ## HACK: hand-optimized bytecode; turn globals into locals
        _PY3=PY3,
        ValueError=ValueError,
        string_types=string_types,
        Decimal=None,
        dict=dict,
        float=float,
        id=id,
        integer_types=integer_types,
        isinstance=isinstance,
        list=list,
        str=str,
        tuple=tuple,
        iter=iter,
    ):
    if _use_decimal and Decimal is None:
        Decimal = decimal.Decimal
    if _item_sort_key and not callable(_item_sort_key):
        raise TypeError("item_sort_key must be None or callable")
    elif _sort_keys and not _item_sort_key:
        _item_sort_key = itemgetter(0)

    if (_int_as_string_bitcount is not None and
        (_int_as_string_bitcount <= 0 or
         not isinstance(_int_as_string_bitcount, integer_types))):
        raise TypeError("int_as_string_bitcount must be a positive integer")

    def _encode_int(value):
        skip_quoting = (
            _int_as_string_bitcount is None
            or
            _int_as_string_bitcount < 1
        )
        if type(value) not in integer_types:
            # See #118, do not trust custom str/repr
            value = int(value)
        if (
            skip_quoting or
            (-1 << _int_as_string_bitcount)
            < value <
            (1 << _int_as_string_bitcount)
        ):
            return str(value)
        return '"' + str(value) + '"'

    def _iterencode_list(lst, _current_indent_level):
        if not lst:
            yield '[]'
            return
        if markers is not None:
            markerid = id(lst)
            if markerid in markers:
                raise ValueError("Circular reference detected")
            markers[markerid] = lst
        buf = '['
        if _indent is not None:
            _current_indent_level += 1
            newline_indent = '\n' + (_indent * _current_indent_level)
            separator = _item_separator + newline_indent
            buf += newline_indent
        else:
            newline_indent = None
            separator = _item_separator
        first = True
        for value in lst:
            if first:
                first = False
            else:
                buf = separator
            if isinstance(value, string_types):
                yield buf + _encoder(value)
            elif _PY3 and isinstance(value, bytes) and _encoding is not None:
                yield buf + _encoder(value)
            elif isinstance(value, RawJSON):
                yield buf + value.encoded_json
            elif value is None:
                yield buf + 'null'
            elif value is True:
                yield buf + 'true'
            elif value is False:
                yield buf + 'false'
            elif isinstance(value, integer_types):
                yield buf + _encode_int(value)
            elif isinstance(value, float):
                yield buf + _floatstr(value)
            elif _use_decimal and isinstance(value, Decimal):
                yield buf + str(value)
            else:
                yield buf
                for_json = _for_json and getattr(value, 'for_json', None)
                if for_json and callable(for_json):
                    chunks = _iterencode(for_json(), _current_indent_level)
                elif isinstance(value, list):
                    chunks = _iterencode_list(value, _current_indent_level)
                else:
                    _asdict = _namedtuple_as_object and getattr(value, '_asdict', None)
                    if _asdict and callable(_asdict):
                        chunks = _iterencode_dict(_asdict(),
                                                  _current_indent_level)
                    elif _tuple_as_array and isinstance(value, tuple):
                        chunks = _iterencode_list(value, _current_indent_level)
                    elif isinstance(value, dict):
                        chunks = _iterencode_dict(value, _current_indent_level)
                    else:
                        chunks = _iterencode(value, _current_indent_level)
                for chunk in chunks:
                    yield chunk
        if first:
            # iterable_as_array misses the fast path at the top
            yield '[]'
        else:
            if newline_indent is not None:
                _current_indent_level -= 1
                yield '\n' + (_indent * _current_indent_level)
            yield ']'
        if markers is not None:
            del markers[markerid]

    def _stringify_key(key):
        if isinstance(key, string_types): # pragma: no cover
            pass
        elif _PY3 and isinstance(key, bytes) and _encoding is not None:
            key = str(key, _encoding)
        elif isinstance(key, float):
            key = _floatstr(key)
        elif key is True:
            key = 'true'
        elif key is False:
            key = 'false'
        elif key is None:
            key = 'null'
        elif isinstance(key, integer_types):
            if type(key) not in integer_types:
                # See #118, do not trust custom str/repr
                key = int(key)
            key = str(key)
        elif _use_decimal and isinstance(key, Decimal):
            key = str(key)
        elif _skipkeys:
            key = None
        else:
            raise TypeError('keys must be str, int, float, bool or None, '
                            'not %s' % key.__class__.__name__)
        return key

    def _iterencode_dict(dct, _current_indent_level):
        if not dct:
            yield '{}'
            return
        if markers is not None:
            markerid = id(dct)
            if markerid in markers:
                raise ValueError("Circular reference detected")
            markers[markerid] = dct
        yield '{'
        if _indent is not None:
            _current_indent_level += 1
            newline_indent = '\n' + (_indent * _current_indent_level)
            item_separator = _item_separator + newline_indent
            yield newline_indent
        else:
            newline_indent = None
            item_separator = _item_separator
        first = True
        if _PY3:
            iteritems = dct.items()
        else:
            iteritems = dct.iteritems()
        if _item_sort_key:
            items = []
            for k, v in dct.items():
                if not isinstance(k, string_types):
                    k = _stringify_key(k)
                    if k is None:
                        continue
                items.append((k, v))
            items.sort(key=_item_sort_key)
        else:
            items = iteritems
        for key, value in items:
            if not (_item_sort_key or isinstance(key, string_types)):
                key = _stringify_key(key)
                if key is None:
                    # _skipkeys must be True
                    continue
            if first:
                first = False
            else:
                yield item_separator
            yield _encoder(key)
            yield _key_separator
            if isinstance(value, string_types):
                yield _encoder(value)
            elif _PY3 and isinstance(value, bytes) and _encoding is not None:
                yield _encoder(value)
            elif isinstance(value, RawJSON):
                yield value.encoded_json
            elif value is None:
                yield 'null'
            elif value is True:
                yield 'true'
            elif value is False:
                yield 'false'
            elif isinstance(value, integer_types):
                yield _encode_int(value)
            elif isinstance(value, float):
                yield _floatstr(value)
            elif _use_decimal and isinstance(value, Decimal):
                yield str(value)
            else:
                for_json = _for_json and getattr(value, 'for_json', None)
                if for_json and callable(for_json):
                    chunks = _iterencode(for_json(), _current_indent_level)
                elif isinstance(value, list):
                    chunks = _iterencode_list(value, _current_indent_level)
                else:
                    _asdict = _namedtuple_as_object and getattr(value, '_asdict', None)
                    if _asdict and callable(_asdict):
                        chunks = _iterencode_dict(_asdict(),
                                                  _current_indent_level)
                    elif _tuple_as_array and isinstance(value, tuple):
                        chunks = _iterencode_list(value, _current_indent_level)
                    elif isinstance(value, dict):
                        chunks = _iterencode_dict(value, _current_indent_level)
                    else:
                        chunks = _iterencode(value, _current_indent_level)
                for chunk in chunks:
                    yield chunk
        if newline_indent is not None:
            _current_indent_level -= 1
            yield '\n' + (_indent * _current_indent_level)
        yield '}'
        if markers is not None:
            del markers[markerid]

    def _iterencode(o, _current_indent_level):
        if isinstance(o, string_types):
            yield _encoder(o)
        elif _PY3 and isinstance(o, bytes) and _encoding is not None:
            yield _encoder(o)
        elif isinstance(o, RawJSON):
            yield o.encoded_json
        elif o is None:
            yield 'null'
        elif o is True:
            yield 'true'
        elif o is False:
            yield 'false'
        elif isinstance(o, integer_types):
            yield _encode_int(o)
        elif isinstance(o, float):
            yield _floatstr(o)
        else:
            for_json = _for_json and getattr(o, 'for_json', None)
            if for_json and callable(for_json):
                for chunk in _iterencode(for_json(), _current_indent_level):
                    yield chunk
            elif isinstance(o, list):
                for chunk in _iterencode_list(o, _current_indent_level):
                    yield chunk
            else:
                _asdict = _namedtuple_as_object and getattr(o, '_asdict', None)
                if _asdict and callable(_asdict):
                    for chunk in _iterencode_dict(_asdict(),
                            _current_indent_level):
                        yield chunk
                elif (_tuple_as_array and isinstance(o, tuple)):
                    for chunk in _iterencode_list(o, _current_indent_level):
                        yield chunk
                elif isinstance(o, dict):
                    for chunk in _iterencode_dict(o, _current_indent_level):
                        yield chunk
                elif _use_decimal and isinstance(o, Decimal):
                    yield str(o)
                else:
                    while _iterable_as_array:
                        # Markers are not checked here because it is valid for
                        # an iterable to return self.
                        try:
                            o = iter(o)
                        except TypeError:
                            break
                        for chunk in _iterencode_list(o, _current_indent_level):
                            yield chunk
                        return
                    if markers is not None:
                        markerid = id(o)
                        if markerid in markers:
                            raise ValueError("Circular reference detected")
                        markers[markerid] = o
                    o = _default(o)
                    for chunk in _iterencode(o, _current_indent_level):
                        yield chunk
                    if markers is not None:
                        del markers[markerid]

    return _iterencode
#from .encoder import JSONEncoder, JSONEncoderForHTML
def _import_OrderedDict():
    import collections
    try:
        return collections.OrderedDict
    except AttributeError:
        from . import ordered_dict
        return ordered_dict.OrderedDict
OrderedDict = _import_OrderedDict()

def _import_c_make_encoder():
    try:
        from ._speedups import make_encoder
        return make_encoder
    except ImportError:
        return None

_default_encoder = JSONEncoder(
    skipkeys=False,
    ensure_ascii=True,
    check_circular=True,
    allow_nan=True,
    indent=None,
    separators=None,
    encoding='utf-8',
    default=None,
    use_decimal=True,
    namedtuple_as_object=True,
    tuple_as_array=True,
    iterable_as_array=False,
    bigint_as_string=False,
    item_sort_key=None,
    for_json=False,
    ignore_nan=False,
    int_as_string_bitcount=None,
)

def dump(obj, fp, skipkeys=False, ensure_ascii=True, check_circular=True,
         allow_nan=True, cls=None, indent=None, separators=None,
         encoding='utf-8', default=None, use_decimal=True,
         namedtuple_as_object=True, tuple_as_array=True,
         bigint_as_string=False, sort_keys=False, item_sort_key=None,
         for_json=False, ignore_nan=False, int_as_string_bitcount=None,
         iterable_as_array=False, **kw):
    """Serialize ``obj`` as a JSON formatted stream to ``fp`` (a
    ``.write()``-supporting file-like object).

    If *skipkeys* is true then ``dict`` keys that are not basic types
    (``str``, ``unicode``, ``int``, ``long``, ``float``, ``bool``, ``None``)
    will be skipped instead of raising a ``TypeError``.

    If *ensure_ascii* is false, then the some chunks written to ``fp``
    may be ``unicode`` instances, subject to normal Python ``str`` to
    ``unicode`` coercion rules. Unless ``fp.write()`` explicitly
    understands ``unicode`` (as in ``codecs.getwriter()``) this is likely
    to cause an error.

    If *check_circular* is false, then the circular reference check
    for container types will be skipped and a circular reference will
    result in an ``OverflowError`` (or worse).

    If *allow_nan* is false, then it will be a ``ValueError`` to
    serialize out of range ``float`` values (``nan``, ``inf``, ``-inf``)
    in strict compliance of the original JSON specification, instead of using
    the JavaScript equivalents (``NaN``, ``Infinity``, ``-Infinity``). See
    *ignore_nan* for ECMA-262 compliant behavior.

    If *indent* is a string, then JSON array elements and object members
    will be pretty-printed with a newline followed by that string repeated
    for each level of nesting. ``None`` (the default) selects the most compact
    representation without any newlines. For backwards compatibility with
    versions of simplejson earlier than 2.1.0, an integer is also accepted
    and is converted to a string with that many spaces.

    If specified, *separators* should be an
    ``(item_separator, key_separator)`` tuple.  The default is ``(', ', ': ')``
    if *indent* is ``None`` and ``(',', ': ')`` otherwise.  To get the most
    compact JSON representation, you should specify ``(',', ':')`` to eliminate
    whitespace.

    *encoding* is the character encoding for str instances, default is UTF-8.

    *default(obj)* is a function that should return a serializable version
    of obj or raise ``TypeError``. The default simply raises ``TypeError``.

    If *use_decimal* is true (default: ``True``) then decimal.Decimal
    will be natively serialized to JSON with full precision.

    If *namedtuple_as_object* is true (default: ``True``),
    :class:`tuple` subclasses with ``_asdict()`` methods will be encoded
    as JSON objects.

    If *tuple_as_array* is true (default: ``True``),
    :class:`tuple` (and subclasses) will be encoded as JSON arrays.

    If *iterable_as_array* is true (default: ``False``),
    any object not in the above table that implements ``__iter__()``
    will be encoded as a JSON array.

    If *bigint_as_string* is true (default: ``False``), ints 2**53 and higher
    or lower than -2**53 will be encoded as strings. This is to avoid the
    rounding that happens in Javascript otherwise. Note that this is still a
    lossy operation that will not round-trip correctly and should be used
    sparingly.

    If *int_as_string_bitcount* is a positive number (n), then int of size
    greater than or equal to 2**n or lower than or equal to -2**n will be
    encoded as strings.

    If specified, *item_sort_key* is a callable used to sort the items in
    each dictionary. This is useful if you want to sort items other than
    in alphabetical order by key. This option takes precedence over
    *sort_keys*.

    If *sort_keys* is true (default: ``False``), the output of dictionaries
    will be sorted by item.

    If *for_json* is true (default: ``False``), objects with a ``for_json()``
    method will use the return value of that method for encoding as JSON
    instead of the object.

    If *ignore_nan* is true (default: ``False``), then out of range
    :class:`float` values (``nan``, ``inf``, ``-inf``) will be serialized as
    ``null`` in compliance with the ECMA-262 specification. If true, this will
    override *allow_nan*.

    To use a custom ``JSONEncoder`` subclass (e.g. one that overrides the
    ``.default()`` method to serialize additional types), specify it with
    the ``cls`` kwarg. NOTE: You should use *default* or *for_json* instead
    of subclassing whenever possible.

    """
    # cached encoder
    if (not skipkeys and ensure_ascii and
        check_circular and allow_nan and
        cls is None and indent is None and separators is None and
        encoding == 'utf-8' and default is None and use_decimal
        and namedtuple_as_object and tuple_as_array and not iterable_as_array
        and not bigint_as_string and not sort_keys
        and not item_sort_key and not for_json
        and not ignore_nan and int_as_string_bitcount is None
        and not kw
    ):
        iterable = _default_encoder.iterencode(obj)
    else:
        if cls is None:
            cls = JSONEncoder
        iterable = cls(skipkeys=skipkeys, ensure_ascii=ensure_ascii,
            check_circular=check_circular, allow_nan=allow_nan, indent=indent,
            separators=separators, encoding=encoding,
            default=default, use_decimal=use_decimal,
            namedtuple_as_object=namedtuple_as_object,
            tuple_as_array=tuple_as_array,
            iterable_as_array=iterable_as_array,
            bigint_as_string=bigint_as_string,
            sort_keys=sort_keys,
            item_sort_key=item_sort_key,
            for_json=for_json,
            ignore_nan=ignore_nan,
            int_as_string_bitcount=int_as_string_bitcount,
            **kw).iterencode(obj)
    # could accelerate with writelines in some versions of Python, at
    # a debuggability cost
    for chunk in iterable:
        fp.write(chunk)


def dumps(obj, skipkeys=False, ensure_ascii=True, check_circular=True,
          allow_nan=True, cls=None, indent=None, separators=None,
          encoding='utf-8', default=None, use_decimal=True,
          namedtuple_as_object=True, tuple_as_array=True,
          bigint_as_string=False, sort_keys=False, item_sort_key=None,
          for_json=False, ignore_nan=False, int_as_string_bitcount=None,
          iterable_as_array=False, **kw):
    """Serialize ``obj`` to a JSON formatted ``str``.

    If ``skipkeys`` is false then ``dict`` keys that are not basic types
    (``str``, ``unicode``, ``int``, ``long``, ``float``, ``bool``, ``None``)
    will be skipped instead of raising a ``TypeError``.

    If ``ensure_ascii`` is false, then the return value will be a
    ``unicode`` instance subject to normal Python ``str`` to ``unicode``
    coercion rules instead of being escaped to an ASCII ``str``.

    If ``check_circular`` is false, then the circular reference check
    for container types will be skipped and a circular reference will
    result in an ``OverflowError`` (or worse).

    If ``allow_nan`` is false, then it will be a ``ValueError`` to
    serialize out of range ``float`` values (``nan``, ``inf``, ``-inf``) in
    strict compliance of the JSON specification, instead of using the
    JavaScript equivalents (``NaN``, ``Infinity``, ``-Infinity``).

    If ``indent`` is a string, then JSON array elements and object members
    will be pretty-printed with a newline followed by that string repeated
    for each level of nesting. ``None`` (the default) selects the most compact
    representation without any newlines. For backwards compatibility with
    versions of simplejson earlier than 2.1.0, an integer is also accepted
    and is converted to a string with that many spaces.

    If specified, ``separators`` should be an
    ``(item_separator, key_separator)`` tuple.  The default is ``(', ', ': ')``
    if *indent* is ``None`` and ``(',', ': ')`` otherwise.  To get the most
    compact JSON representation, you should specify ``(',', ':')`` to eliminate
    whitespace.

    ``encoding`` is the character encoding for str instances, default is UTF-8.

    ``default(obj)`` is a function that should return a serializable version
    of obj or raise TypeError. The default simply raises TypeError.

    If *use_decimal* is true (default: ``True``) then decimal.Decimal
    will be natively serialized to JSON with full precision.

    If *namedtuple_as_object* is true (default: ``True``),
    :class:`tuple` subclasses with ``_asdict()`` methods will be encoded
    as JSON objects.

    If *tuple_as_array* is true (default: ``True``),
    :class:`tuple` (and subclasses) will be encoded as JSON arrays.

    If *iterable_as_array* is true (default: ``False``),
    any object not in the above table that implements ``__iter__()``
    will be encoded as a JSON array.

    If *bigint_as_string* is true (not the default), ints 2**53 and higher
    or lower than -2**53 will be encoded as strings. This is to avoid the
    rounding that happens in Javascript otherwise.

    If *int_as_string_bitcount* is a positive number (n), then int of size
    greater than or equal to 2**n or lower than or equal to -2**n will be
    encoded as strings.

    If specified, *item_sort_key* is a callable used to sort the items in
    each dictionary. This is useful if you want to sort items other than
    in alphabetical order by key. This option takes precendence over
    *sort_keys*.

    If *sort_keys* is true (default: ``False``), the output of dictionaries
    will be sorted by item.

    If *for_json* is true (default: ``False``), objects with a ``for_json()``
    method will use the return value of that method for encoding as JSON
    instead of the object.

    If *ignore_nan* is true (default: ``False``), then out of range
    :class:`float` values (``nan``, ``inf``, ``-inf``) will be serialized as
    ``null`` in compliance with the ECMA-262 specification. If true, this will
    override *allow_nan*.

    To use a custom ``JSONEncoder`` subclass (e.g. one that overrides the
    ``.default()`` method to serialize additional types), specify it with
    the ``cls`` kwarg. NOTE: You should use *default* instead of subclassing
    whenever possible.

    """
    # cached encoder
    if (not skipkeys and ensure_ascii and
        check_circular and allow_nan and
        cls is None and indent is None and separators is None and
        encoding == 'utf-8' and default is None and use_decimal
        and namedtuple_as_object and tuple_as_array and not iterable_as_array
        and not bigint_as_string and not sort_keys
        and not item_sort_key and not for_json
        and not ignore_nan and int_as_string_bitcount is None
        and not kw
    ):
        return _default_encoder.encode(obj)
    if cls is None:
        cls = JSONEncoder
    return cls(
        skipkeys=skipkeys, ensure_ascii=ensure_ascii,
        check_circular=check_circular, allow_nan=allow_nan, indent=indent,
        separators=separators, encoding=encoding, default=default,
        use_decimal=use_decimal,
        namedtuple_as_object=namedtuple_as_object,
        tuple_as_array=tuple_as_array,
        iterable_as_array=iterable_as_array,
        bigint_as_string=bigint_as_string,
        sort_keys=sort_keys,
        item_sort_key=item_sort_key,
        for_json=for_json,
        ignore_nan=ignore_nan,
        int_as_string_bitcount=int_as_string_bitcount,
        **kw).encode(obj)


_default_decoder = JSONDecoder(encoding=None, object_hook=None,
                               object_pairs_hook=None)


def load(fp, encoding=None, cls=None, object_hook=None, parse_float=None,
        parse_int=None, parse_constant=None, object_pairs_hook=None,
        use_decimal=False, namedtuple_as_object=True, tuple_as_array=True,
        **kw):
    """Deserialize ``fp`` (a ``.read()``-supporting file-like object containing
    a JSON document) to a Python object.

    *encoding* determines the encoding used to interpret any
    :class:`str` objects decoded by this instance (``'utf-8'`` by
    default).  It has no effect when decoding :class:`unicode` objects.

    Note that currently only encodings that are a superset of ASCII work,
    strings of other encodings should be passed in as :class:`unicode`.

    *object_hook*, if specified, will be called with the result of every
    JSON object decoded and its return value will be used in place of the
    given :class:`dict`.  This can be used to provide custom
    deserializations (e.g. to support JSON-RPC class hinting).

    *object_pairs_hook* is an optional function that will be called with
    the result of any object literal decode with an ordered list of pairs.
    The return value of *object_pairs_hook* will be used instead of the
    :class:`dict`.  This feature can be used to implement custom decoders
    that rely on the order that the key and value pairs are decoded (for
    example, :func:`collections.OrderedDict` will remember the order of
    insertion). If *object_hook* is also defined, the *object_pairs_hook*
    takes priority.

    *parse_float*, if specified, will be called with the string of every
    JSON float to be decoded.  By default, this is equivalent to
    ``float(num_str)``. This can be used to use another datatype or parser
    for JSON floats (e.g. :class:`decimal.Decimal`).

    *parse_int*, if specified, will be called with the string of every
    JSON int to be decoded.  By default, this is equivalent to
    ``int(num_str)``.  This can be used to use another datatype or parser
    for JSON integers (e.g. :class:`float`).

    *parse_constant*, if specified, will be called with one of the
    following strings: ``'-Infinity'``, ``'Infinity'``, ``'NaN'``.  This
    can be used to raise an exception if invalid JSON numbers are
    encountered.

    If *use_decimal* is true (default: ``False``) then it implies
    parse_float=decimal.Decimal for parity with ``dump``.

    To use a custom ``JSONDecoder`` subclass, specify it with the ``cls``
    kwarg. NOTE: You should use *object_hook* or *object_pairs_hook* instead
    of subclassing whenever possible.

    """
    return loads(fp.read(),
        encoding=encoding, cls=cls, object_hook=object_hook,
        parse_float=parse_float, parse_int=parse_int,
        parse_constant=parse_constant, object_pairs_hook=object_pairs_hook,
        use_decimal=use_decimal, **kw)


def loads(s, encoding=None, cls=None, object_hook=None, parse_float=None,
        parse_int=None, parse_constant=None, object_pairs_hook=None,
        use_decimal=False, **kw):
    """Deserialize ``s`` (a ``str`` or ``unicode`` instance containing a JSON
    document) to a Python object.

    *encoding* determines the encoding used to interpret any
    :class:`str` objects decoded by this instance (``'utf-8'`` by
    default).  It has no effect when decoding :class:`unicode` objects.

    Note that currently only encodings that are a superset of ASCII work,
    strings of other encodings should be passed in as :class:`unicode`.

    *object_hook*, if specified, will be called with the result of every
    JSON object decoded and its return value will be used in place of the
    given :class:`dict`.  This can be used to provide custom
    deserializations (e.g. to support JSON-RPC class hinting).

    *object_pairs_hook* is an optional function that will be called with
    the result of any object literal decode with an ordered list of pairs.
    The return value of *object_pairs_hook* will be used instead of the
    :class:`dict`.  This feature can be used to implement custom decoders
    that rely on the order that the key and value pairs are decoded (for
    example, :func:`collections.OrderedDict` will remember the order of
    insertion). If *object_hook* is also defined, the *object_pairs_hook*
    takes priority.

    *parse_float*, if specified, will be called with the string of every
    JSON float to be decoded.  By default, this is equivalent to
    ``float(num_str)``. This can be used to use another datatype or parser
    for JSON floats (e.g. :class:`decimal.Decimal`).

    *parse_int*, if specified, will be called with the string of every
    JSON int to be decoded.  By default, this is equivalent to
    ``int(num_str)``.  This can be used to use another datatype or parser
    for JSON integers (e.g. :class:`float`).

    *parse_constant*, if specified, will be called with one of the
    following strings: ``'-Infinity'``, ``'Infinity'``, ``'NaN'``.  This
    can be used to raise an exception if invalid JSON numbers are
    encountered.

    If *use_decimal* is true (default: ``False``) then it implies
    parse_float=decimal.Decimal for parity with ``dump``.

    To use a custom ``JSONDecoder`` subclass, specify it with the ``cls``
    kwarg. NOTE: You should use *object_hook* or *object_pairs_hook* instead
    of subclassing whenever possible.

    """
    if (cls is None and encoding is None and object_hook is None and
            parse_int is None and parse_float is None and
            parse_constant is None and object_pairs_hook is None
            and not use_decimal and not kw):
        return _default_decoder.decode(s)
    if cls is None:
        cls = JSONDecoder
    if object_hook is not None:
        kw['object_hook'] = object_hook
    if object_pairs_hook is not None:
        kw['object_pairs_hook'] = object_pairs_hook
    if parse_float is not None:
        kw['parse_float'] = parse_float
    if parse_int is not None:
        kw['parse_int'] = parse_int
    if parse_constant is not None:
        kw['parse_constant'] = parse_constant
    if use_decimal:
        if parse_float is not None:
            raise TypeError("use_decimal=True implies parse_float=Decimal")
        kw['parse_float'] = Decimal
    return cls(encoding=encoding, **kw).decode(s)

def simple_first(kv):
    """Helper function to pass to item_sort_key to sort simple
    elements to the top, then container elements.
    """
    return (isinstance(kv[1], (list, dict, tuple)), kv[0])

def from_json(s):
    return loads(s)

def main(input):
	return from_json(input)

if __name__ == "__main__":
	print(main(sys.argv[1]))

def default_iterable(obj):
    return list(obj)

def _dicts():
    dct1 = {
        'key1': 'value1'
    }

    dct2 = {
        'key2': 'value2',
        'd1': dct1
    }

    dct3 = {
        'key2': 'value2',
        'd1': dumps(dct1)
    }

    dct4 = {
        'key2': 'value2',
        'd1': RawJSON(dumps(dct1))
    }
    return dct1, dct2, dct3, dct4

class JSONTestObject:
    pass

class RecursiveJSONEncoder(JSONEncoder):
    recurse = False
    def default(self, o):
        if o is JSONTestObject:
            if self.recurse:
                return [JSONTestObject]
            else:
                return 'JSONTestObject'
        return JSONEncoder.default(o)


class MisbehavingBytesSubtype(binary_type):
    def decode(self, encoding=None):
        return "bad decode"
    def __str__(self):
        return "bad __str__"
    def __bytes__(self):
        return b("bad __bytes__")

class MisbehavingTextSubtype(text_type):
    def __str__(self):
        return "FAIL!"

def as_text_type(s):
    if PY3 and isinstance(s, bytes):
        return s.decode('ascii')
    return s

def decode_iso_8859_15(b):
    return b.decode('iso-8859-15')

class ForJson(object):
    def for_json(self):
        return {'for_json': 1}


class NestedForJson(object):
    def for_json(self):
        return {'nested': ForJson()}


class ForJsonList(object):
    def for_json(self):
        return ['list']


class DictForJson(dict):
    def for_json(self):
        return {'alpha': 1}


class ListForJson(list):
    def for_json(self):
        return ['list']

def iter_dumps(obj, **kw):
    return ''.join(JSONEncoder(**kw).iterencode(obj))

def sio_dump(obj, **kw):
    sio = StringIO()
    dumps(obj, **kw)
    return sio.getvalue()

class BadBool:
    def __bool__(self):
        1/0
    __nonzero__ = __bool__

class WonkyTextSubclass(text_type):
    def __getslice__(self, start, end):
        return self.__class__('not what you wanted!')

class AlternateInt(int):
    def __repr__(self):
        return 'invalid json'
    __str__ = __repr__


class AlternateFloat(float):
    def __repr__(self):
        return 'invalid json'
    __str__ = __repr__

import os
import codecs
import subprocess
import tempfile
try:
    # Python 3.x
    from test.support import strip_python_stderr
except ImportError:
    # Python 2.6+
    try:
        from test.test_support import strip_python_stderr
    except ImportError:
        # Python 2.5
        import re
        def strip_python_stderr(stderr):
            return re.sub(
                r"\[\d+ refs\]\r?\n?$".encode(),
                "".encode(),
                stderr).strip()

def open_temp_file():
    if sys.version_info >= (2, 6):
        file = tempfile.NamedTemporaryFile(delete=False)
        filename = file.name
    else:
        fd, filename = tempfile.mkstemp()
        file = os.fdopen(fd, 'w+b')
    return file, filename

# 2007-10-05
JSONDOCS = [
    # http://json.org/JSON_checker/test/fail1.json
    '"A JSON payload should be an object or array, not a string."',
    # http://json.org/JSON_checker/test/fail2.json
    '["Unclosed array"',
    # http://json.org/JSON_checker/test/fail3.json
    '{unquoted_key: "keys must be quoted"}',
    # http://json.org/JSON_checker/test/fail4.json
    '["extra comma",]',
    # http://json.org/JSON_checker/test/fail5.json
    '["double extra comma",,]',
    # http://json.org/JSON_checker/test/fail6.json
    '[   , "<-- missing value"]',
    # http://json.org/JSON_checker/test/fail7.json
    '["Comma after the close"],',
    # http://json.org/JSON_checker/test/fail8.json
    '["Extra close"]]',
    # http://json.org/JSON_checker/test/fail9.json
    '{"Extra comma": true,}',
    # http://json.org/JSON_checker/test/fail10.json
    '{"Extra value after close": true} "misplaced quoted value"',
    # http://json.org/JSON_checker/test/fail11.json
    '{"Illegal expression": 1 + 2}',
    # http://json.org/JSON_checker/test/fail12.json
    '{"Illegal invocation": alert()}',
    # http://json.org/JSON_checker/test/fail13.json
    '{"Numbers cannot have leading zeroes": 013}',
    # http://json.org/JSON_checker/test/fail14.json
    '{"Numbers cannot be hex": 0x14}',
    # http://json.org/JSON_checker/test/fail15.json
    '["Illegal backslash escape: \\x15"]',
    # http://json.org/JSON_checker/test/fail16.json
    '[\\naked]',
    # http://json.org/JSON_checker/test/fail17.json
    '["Illegal backslash escape: \\017"]',
    # http://json.org/JSON_checker/test/fail18.json
    '[[[[[[[[[[[[[[[[[[[["Too deep"]]]]]]]]]]]]]]]]]]]]',
    # http://json.org/JSON_checker/test/fail19.json
    '{"Missing colon" null}',
    # http://json.org/JSON_checker/test/fail20.json
    '{"Double colon":: null}',
    # http://json.org/JSON_checker/test/fail21.json
    '{"Comma instead of colon", null}',
    # http://json.org/JSON_checker/test/fail22.json
    '["Colon instead of comma": false]',
    # http://json.org/JSON_checker/test/fail23.json
    '["Bad value", truth]',
    # http://json.org/JSON_checker/test/fail24.json
    "['single quote']",
    # http://json.org/JSON_checker/test/fail25.json
    '["\ttab\tcharacter\tin\tstring\t"]',
    # http://json.org/JSON_checker/test/fail26.json
    '["tab\\   character\\   in\\  string\\  "]',
    # http://json.org/JSON_checker/test/fail27.json
    '["line\nbreak"]',
    # http://json.org/JSON_checker/test/fail28.json
    '["line\\\nbreak"]',
    # http://json.org/JSON_checker/test/fail29.json
    '[0e]',
    # http://json.org/JSON_checker/test/fail30.json
    '[0e+]',
    # http://json.org/JSON_checker/test/fail31.json
    '[0e+-1]',
    # http://json.org/JSON_checker/test/fail32.json
    '{"Comma instead if closing brace": true,',
    # http://json.org/JSON_checker/test/fail33.json
    '["mismatch"}',
    # http://code.google.com/p/simplejson/issues/detail?id=3
    u'["A\u001FZ control characters in string"]',
    # misc based on coverage
    '{',
    '{]',
    '{"foo": "bar"]',
    '{"foo": "bar"',
    'nul',
    'nulx',
    '-',
    '-x',
    '-e',
    '-e0',
    '-Infinite',
    '-Inf',
    'Infinit',
    'Infinite',
    'NaM',
    'NuN',
    'falsy',
    'fal',
    'trug',
    'tru',
    '1e',
    '1ex',
    '1e-',
    '1e-x',
]

SKIPS = {
    1: "why not have a string payload?",
    18: "spec doesn't specify any nesting limitations",
}

JSON1 = r'''
[
    "JSON Test Pattern pass1",
    {"object with 1 member":["array with 1 element"]},
    {},
    [],
    -42,
    true,
    false,
    null,
    {
        "integer": 1234567890,
        "real": -9876.543210,
        "e": 0.123456789e-12,
        "E": 1.234567890E+34,
        "":  23456789012E66,
        "zero": 0,
        "one": 1,
        "space": " ",
        "quote": "\"",
        "backslash": "\\",
        "controls": "\b\f\n\r\t",
        "slash": "/ & \/",
        "alpha": "abcdefghijklmnopqrstuvwyz",
        "ALPHA": "ABCDEFGHIJKLMNOPQRSTUVWYZ",
        "digit": "0123456789",
        "special": "`1~!@#$%^&*()_+-={':[,]}|;.</>?",
        "hex": "\u0123\u4567\u89AB\uCDEF\uabcd\uef4A",
        "true": true,
        "false": false,
        "null": null,
        "array":[  ],
        "object":{  },
        "address": "50 St. James Street",
        "url": "http://www.JSON.org/",
        "comment": "// /* <!-- --",
        "# -- --> */": " ",
        " s p a c e d " :[1,2 , 3

,

4 , 5        ,          6           ,7        ],"compact": [1,2,3,4,5,6,7],
        "jsontext": "{\"object with 1 member\":[\"array with 1 element\"]}",
        "quotes": "&#34; \u0022 %22 0x22 034 &#x22;",
        "\/\\\"\uCAFE\uBABE\uAB98\uFCDE\ubcda\uef4A\b\f\n\r\t`1~!@#$%^&*()_+-=[]{}|;:',./<>?"
: "A key can be any string"
    },
    0.5 ,98.6
,
99.44
,

1066,
1e1,
0.1e1,
1e-1,
1e00,2e+00,2e-00
,"rosebud"]
'''

JSON2 = r'''
[[[[[[[[[[[[[[[[[[["Not too deep"]]]]]]]]]]]]]]]]]]]
'''

JSON3 = r'''
{
    "JSON Test Pattern pass3": {
        "The outermost value": "must be an object or array.",
        "In this test": "It is an object."
    }
}
'''

import unittest
from operator import itemgetter
import pickle, math, textwrap

try:
    from collections import namedtuple
except ImportError:
    class Value(tuple):
        def __new__(cls, *args):
            return tuple.__new__(cls, args)

        def _asdict(self):
            return {'value': self[0]}
    class Point(tuple):
        def __new__(cls, *args):
            return tuple.__new__(cls, args)

        def _asdict(self):
            return {'x': self[0], 'y': self[1]}
else:
    Value = namedtuple('Value', ['value'])
    Point = namedtuple('Point', ['x', 'y'])

class DuckValue(object):
    def __init__(self, *args):
        self.value = Value(*args)

    def _asdict(self):
        return self.value._asdict()

class DuckPoint(object):
    def __init__(self, *args):
        self.point = Point(*args)

    def _asdict(self):
        return self.point._asdict()

class DeadDuck(object):
    _asdict = None

class DeadDict(dict):
    _asdict = None

CONSTRUCTORS = [
    lambda v: v,
    lambda v: [v],
    lambda v: [{'key': v}],
]

class TestAll(unittest.TestCase):
    # Python 2.5, at least the one that ships on Mac OS X, calculates
    # 2 ** 53 as 0! It manages to calculate 1 << 53 correctly.
    values = [(200, 200),
              ((1 << 53) - 1, 9007199254740991),
              ((1 << 53), '9007199254740992'),
              ((1 << 53) + 1, '9007199254740993'),
              (-100, -100),
              ((-1 << 53), '-9007199254740992'),
              ((-1 << 53) - 1, '-9007199254740993'),
              ((-1 << 53) + 1, -9007199254740991)]

    options = (
        {"bigint_as_string": True},
        {"int_as_string_bitcount": 53}
    )

    def test_ints(self):
        for opts in self.options:
            for val, expect in self.values:
                self.assertEqual(
                    val,
                    loads(dumps(val)))
                self.assertEqual(
                    expect,
                    loads(dumps(val, **opts)))

    def test_lists(self):
        for opts in self.options:
            for val, expect in self.values:
                val = [val, val]
                expect = [expect, expect]
                self.assertEqual(
                    val,
                    loads(dumps(val)))
                self.assertEqual(
                    expect,
                    loads(dumps(val, **opts)))

    def test_dicts(self):
        for opts in self.options:
            for val, expect in self.values:
                val = {'k': val}
                expect = {'k': expect}
                self.assertEqual(
                    val,
                    loads(dumps(val)))
                self.assertEqual(
                    expect,
                    loads(dumps(val, **opts)))

    def test_dict_keys(self):
        for opts in self.options:
            for val, _ in self.values:
                expect = {str(val): 'value'}
                val = {val: 'value'}
                self.assertEqual(
                    expect,
                    loads(dumps(val)))
                self.assertEqual(
                    expect,
                    loads(dumps(val, **opts)))

    # Python 2.5, at least the one that ships on Mac OS X, calculates
    # 2 ** 31 as 0! It manages to calculate 1 << 31 correctly.
    values1 = [
        (200, 200),
        ((1 << 31) - 1, (1 << 31) - 1),
        ((1 << 31), str(1 << 31)),
        ((1 << 31) + 1, str((1 << 31) + 1)),
        (-100, -100),
        ((-1 << 31), str(-1 << 31)),
        ((-1 << 31) - 1, str((-1 << 31) - 1)),
        ((-1 << 31) + 1, (-1 << 31) + 1),
    ]

    def test_invalid_counts_1(self):
        for n in ['foo', -1, 0, 1.0]:
            self.assertRaises(
                TypeError,
                dumps, 0, int_as_string_bitcount=n)

    def test_ints_outside_range_fails_1(self):
        self.assertNotEqual(
            str(1 << 15),
            loads(dumps(1 << 15, int_as_string_bitcount=16)),
            )

    def test_ints_1(self):
        for val, expect in self.values1:
            self.assertEqual(
                val,
                loads(dumps(val)))
            self.assertEqual(
                expect,
                loads(dumps(val, int_as_string_bitcount=31)),
                )

    def test_lists_1(self):
        for val, expect in self.values1:
            val = [val, val]
            expect = [expect, expect]
            self.assertEqual(
                val,
                loads(dumps(val)))
            self.assertEqual(
                expect,
                loads(dumps(val, int_as_string_bitcount=31)))

    def test_dicts_1(self):
        for val, expect in self.values1:
            val = {'k': val}
            expect = {'k': expect}
            self.assertEqual(
                val,
                loads(dumps(val)))
            self.assertEqual(
                expect,
                loads(dumps(val, int_as_string_bitcount=31)))

    def test_dict_keys_1(self):
        for val, _ in self.values1:
            expect = {str(val): 'value'}
            val = {val: 'value'}
            self.assertEqual(
                expect,
                loads(dumps(val)))
            self.assertEqual(
                expect,
                loads(dumps(val, int_as_string_bitcount=31)))

    def test_circular_dict_2(self):
        dct1, dct2, dct3, dct4 = _dicts()
        dct = {}
        dct['a'] = dct
        self.assertRaises(ValueError, dumps, dct)

    def test_circular_list_2(self):
        lst = []
        lst.append(lst)
        self.assertRaises(ValueError, dumps, lst)

    def test_circular_composite_2(self):
        dct1, dct2, dct3, dct4 = _dicts()
        dct2 = {}
        dct2['a'] = []
        dct2['a'].append(dct2)
        self.assertRaises(ValueError, dumps, dct2)

    def test_circular_default_2(self):
        dumps([set()], default=default_iterable)
        self.assertRaises(TypeError, dumps, [set()])

    def test_circular_off_default(self):
        dumps([set()], default=default_iterable, check_circular=False)
        self.assertRaises(TypeError, dumps, [set()], check_circular=False)

    NUMS = "1.0", "10.00", "1.1", "1234567890.1234567890", "500"
    def dumps(self, obj, **kw):
        sio = StringIO()
        dump(obj, sio, **kw)
        res = dumps(obj, **kw)
        self.assertEqual(res, sio.getvalue())
        return res

    def loads(self, s, **kw):
        sio = StringIO(s)
        res = loads(s, **kw)
        self.assertEqual(res, load(sio, **kw))
        return res

    def test_decimal_encode(self):
        for d in map(Decimal, self.NUMS):
            self.assertEqual(self.dumps(d, use_decimal=True), str(d))

    def test_decimal_decode(self):
        for s in self.NUMS:
            self.assertEqual(self.loads(s, parse_float=Decimal), Decimal(s))

    def test_stringify_key(self):
        for d in map(Decimal, self.NUMS):
            v = {d: d}
            self.assertEqual(
                self.loads(
                    self.dumps(v, use_decimal=True), parse_float=Decimal),
                {str(d): d})

    def test_decimal_roundtrip(self):
        for d in map(Decimal, self.NUMS):
            # The type might not be the same (int and Decimal) but they
            # should still compare equal.
            for v in [d, [d], {'': d}]:
                self.assertEqual(
                    self.loads(
                        self.dumps(v, use_decimal=True), parse_float=Decimal),
                    v)

    def test_decimal_defaults(self):
        d = Decimal('1.1')
        # use_decimal=True is the default
        self.assertRaises(TypeError, dumps, d, use_decimal=False)
        self.assertEqual('1.1', dumps(d))
        self.assertEqual('1.1', dumps(d, use_decimal=True))
        self.assertRaises(TypeError, dump, d, StringIO(),
                          use_decimal=False)
        sio = StringIO()
        dump(d, sio)
        self.assertEqual('1.1', sio.getvalue())
        sio = StringIO()
        dump(d, sio, use_decimal=True)
        self.assertEqual('1.1', sio.getvalue())

    def test_decimal_reload(self):
        # Simulate a subinterpreter that reloads the Python modules but not
        # the C code https://github.com/simplejson/simplejson/issues/34
        global Decimal
        Decimal = reload_module(decimal).Decimal
        #import simplejson.encoder
        self.test_decimal_roundtrip()

    if not hasattr(unittest.TestCase, 'assertIs'):
        def assertIs(self, a, b):
            self.assertTrue(a is b, '%r is %r' % (a, b))

    def test_decimal_4(self):
        rval = loads('1.1', parse_float=decimal.Decimal)
        self.assertTrue(isinstance(rval, decimal.Decimal))
        self.assertEqual(rval, decimal.Decimal('1.1'))

    def test_float_4(self):
        rval = loads('1', parse_int=float)
        self.assertTrue(isinstance(rval, float))
        self.assertEqual(rval, 1.0)

    def test_decoder_optimizations_4(self):
        # Several optimizations were made that skip over calls to
        # the whitespace regex, so this test is designed to try and
        # exercise the uncommon cases. The array cases are already covered.
        rval = loads('{   "key"    :    "value"    ,  "k":"v"    }')
        self.assertEqual(rval, {"key":"value", "k":"v"})

    def test_empty_objects_4(self):
        s = '{}'
        self.assertEqual(loads(s), eval(s))
        s = '[]'
        self.assertEqual(loads(s), eval(s))
        s = '""'
        self.assertEqual(loads(s), eval(s))

    def test_object_pairs_hook_4(self):
        s = '{"xkd":1, "kcw":2, "art":3, "hxm":4, "qrt":5, "pad":6, "hoy":7}'
        p = [("xkd", 1), ("kcw", 2), ("art", 3), ("hxm", 4),
             ("qrt", 5), ("pad", 6), ("hoy", 7)]
        self.assertEqual(loads(s), eval(s))
        self.assertEqual(loads(s, object_pairs_hook=lambda x: x), p)
        self.assertEqual(load(StringIO(s),
                                   object_pairs_hook=lambda x: x), p)
        od = loads(s, object_pairs_hook=OrderedDict)
        self.assertEqual(od, OrderedDict(p))
        self.assertEqual(type(od), OrderedDict)
        # the object_pairs_hook takes priority over the object_hook
        self.assertEqual(loads(s,
                                    object_pairs_hook=OrderedDict,
                                    object_hook=lambda x: None),
                         OrderedDict(p))

    def check_keys_reuse(self, source, loads):
        rval = loads(source)
        (a, b), (c, d) = sorted(rval[0]), sorted(rval[1])
        self.assertIs(a, c)
        self.assertIs(b, d)

    def test_keys_reuse_str_4(self):
        s = u'[{"a_key": 1, "b_\xe9": 2}, {"a_key": 3, "b_\xe9": 4}]'.encode('utf8')
        self.check_keys_reuse(s, loads)

    def test_keys_reuse_unicode_4(self):
        s = u'[{"a_key": 1, "b_\xe9": 2}, {"a_key": 3, "b_\xe9": 4}]'
        self.check_keys_reuse(s, loads)

    def test_empty_strings_4(self):
        self.assertEqual(loads('""'), "")
        self.assertEqual(loads(u'""'), u"")
        self.assertEqual(loads('[""]'), [""])
        self.assertEqual(loads(u'[""]'), [u""])

    def test_raw_decode_4(self):
        cls = JSONDecoder
        self.assertEqual(
            ({'a': {}}, 9),
            cls().raw_decode("{\"a\": {}}"))
        # http://code.google.com/p/simplejson/issues/detail?id=85
        self.assertEqual(
            ({'a': {}}, 9),
            cls(object_pairs_hook=dict).raw_decode("{\"a\": {}}"))
        # https://github.com/simplejson/simplejson/pull/38
        self.assertEqual(
            ({'a': {}}, 11),
            cls().raw_decode(" \n{\"a\": {}}"))

    def test_bytes_decode_4(self):
        cls = JSONDecoder
        data = b('"\xe2\x82\xac"')
        self.assertEqual(cls().decode(data), u'\u20ac')
        self.assertEqual(cls(encoding='latin1').decode(data), u'\xe2\x82\xac')
        self.assertEqual(cls(encoding=None).decode(data), u'\u20ac')

        data = MisbehavingBytesSubtype(b('"\xe2\x82\xac"'))
        self.assertEqual(cls().decode(data), u'\u20ac')
        self.assertEqual(cls(encoding='latin1').decode(data), u'\xe2\x82\xac')
        self.assertEqual(cls(encoding=None).decode(data), u'\u20ac')

    def test_bounds_checking_4(self):
        # https://github.com/simplejson/simplejson/issues/98
        j = JSONDecoder()
        for i in [4, 5, 6, -1, -2, -3, -4, -5, -6]:
            self.assertRaises(ValueError, j.scan_once, '1234', i)
            self.assertRaises(ValueError, j.raw_decode, '1234', i)
        x, y = sorted(['128931233', '472389423'], key=id)
        diff = id(x) - id(y)
        self.assertRaises(ValueError, j.scan_once, y, diff)
        self.assertRaises(ValueError, j.raw_decode, y, i)

    def test_default(self):
        self.assertEqual(
            dumps(type, default=repr),
            dumps(repr(type)))

    def test_dump_5(self):
        sio = StringIO()
        dump({}, sio)
        self.assertEqual(sio.getvalue(), '{}')

    def test_constants_5(self):
        for c in [None, True, False]:
            self.assertTrue(loads(dumps(c)) is c)
            self.assertTrue(loads(dumps([c]))[0] is c)
            self.assertTrue(loads(dumps({'a': c}))['a'] is c)

    def test_stringify_key_5(self):
        items = [(b('bytes'), 'bytes'),
                 (1.0, '1.0'),
                 (10, '10'),
                 (True, 'true'),
                 (False, 'false'),
                 (None, 'null'),
                 (long_type(100), '100')]
        for k, expect in items:
            self.assertEqual(
                loads(dumps({k: expect})),
                {expect: expect})
            self.assertEqual(
                loads(dumps({k: expect}, sort_keys=True)),
                {expect: expect})

    def test_dumps_5(self):
        self.assertEqual(dumps({}), '{}')

    def test_encode_truefalse_5(self):
        self.assertEqual(dumps(
                 {True: False, False: True}, sort_keys=True),
                 '{"false": true, "true": false}')
        self.assertEqual(
            dumps(
                {2: 3.0,
                 4.0: long_type(5),
                 False: 1,
                 long_type(6): True,
                 "7": 0},
                sort_keys=True),
            '{"2": 3.0, "4.0": 5, "6": true, "7": 0, "false": 1}')

    def test_ordered_dict_5(self):
        # http://bugs.python.org/issue6105
        items = [('one', 1), ('two', 2), ('three', 3), ('four', 4), ('five', 5)]
        s = dumps(OrderedDict(items))
        self.assertEqual(
            s,
            '{"one": 1, "two": 2, "three": 3, "four": 4, "five": 5}')

    def test_indent_unknown_type_acceptance_5(self):
        """
        A test against the regression mentioned at `github issue 29`_.

        The indent parameter should accept any type which pretends to be
        an instance of int or long when it comes to being multiplied by
        strings, even if it is not actually an int or long, for
        backwards compatibility.

        .. _github issue 29:
           http://github.com/simplejson/simplejson/issue/29
        """

        class AwesomeInt(object):
            """An awesome reimplementation of integers"""

            def __init__(self, *args, **kwargs):
                if len(args) > 0:
                    # [construct from literals, objects, etc.]
                    # ...

                    # Finally, if args[0] is an integer, store it
                    if isinstance(args[0], int):
                        self._int = args[0]

            # [various methods]

            def __mul__(self, other):
                # [various ways to multiply AwesomeInt objects]
                # ... finally, if the right-hand operand is not awesome enough,
                # try to do a normal integer multiplication
                if hasattr(self, '_int'):
                    return self._int * other
                else:
                    raise NotImplementedError("To do non-awesome things with"
                        " this object, please construct it from an integer!")

        s = dumps([0, 1, 2], indent=AwesomeInt(3))
        self.assertEqual(s, '[\n   0,\n   1,\n   2\n]')

    def test_accumulator_5(self):
        # the C API uses an accumulator that collects after 100,000 appends
        lst = [0] * 100000
        self.assertEqual(loads(dumps(lst)), lst)

    def test_sort_keys_5(self):
        # https://github.com/simplejson/simplejson/issues/106
        for num_keys in range(2, 32):
            p = dict((str(x), x) for x in range(num_keys))
            sio = StringIO()
            dump(p, sio, sort_keys=True)
            self.assertEqual(sio.getvalue(), dumps(p, sort_keys=True))
            self.assertEqual(loads(sio.getvalue()), p)

    def test_misbehaving_text_subtype_5(self):
        # https://github.com/simplejson/simplejson/issues/185
        text = "this is some text"
        self.assertEqual(
            dumps(MisbehavingTextSubtype(text)),
            dumps(text)
        )
        self.assertEqual(
            dumps([MisbehavingTextSubtype(text)]),
            dumps([text])
        )
        self.assertEqual(
            dumps({MisbehavingTextSubtype(text): 42}),
            dumps({text: 42})
        )

    def test_misbehaving_bytes_subtype_5(self):
        data = b("this is some data \xe2\x82\xac")
        self.assertEqual(
            dumps(MisbehavingBytesSubtype(data)),
            dumps(data)
        )
        self.assertEqual(
            dumps([MisbehavingBytesSubtype(data)]),
            dumps([data])
        )
        self.assertEqual(
            dumps({MisbehavingBytesSubtype(data): 42}),
            dumps({data: 42})
        )

    def test_bytes_toplevel_5(self):
        self.assertEqual(dumps(b('\xe2\x82\xac')), r'"\u20ac"')
        self.assertRaises(UnicodeDecodeError, dumps, b('\xa4'))
        self.assertEqual(dumps(b('\xa4'), encoding='iso-8859-1'),
                         r'"\u00a4"')
        self.assertEqual(dumps(b('\xa4'), encoding='iso-8859-15'),
                         r'"\u20ac"')
        if PY3:
            self.assertRaises(TypeError, dumps, b('\xe2\x82\xac'),
                              encoding=None)
            self.assertRaises(TypeError, dumps, b('\xa4'),
                              encoding=None)
            self.assertEqual(dumps(b('\xa4'), encoding=None,
                                        default=decode_iso_8859_15),
                            r'"\u20ac"')
        else:
            self.assertEqual(dumps(b('\xe2\x82\xac'), encoding=None),
                             r'"\u20ac"')
            self.assertRaises(UnicodeDecodeError, dumps, b('\xa4'),
                              encoding=None)
            self.assertRaises(UnicodeDecodeError, dumps, b('\xa4'),
                              encoding=None, default=decode_iso_8859_15)

    def test_bytes_nested_5(self):
        self.assertEqual(dumps([b('\xe2\x82\xac')]), r'["\u20ac"]')
        self.assertRaises(UnicodeDecodeError, dumps, [b('\xa4')])
        self.assertEqual(dumps([b('\xa4')], encoding='iso-8859-1'),
                         r'["\u00a4"]')
        self.assertEqual(dumps([b('\xa4')], encoding='iso-8859-15'),
                         r'["\u20ac"]')
        if PY3:
            self.assertRaises(TypeError, dumps, [b('\xe2\x82\xac')],
                              encoding=None)
            self.assertRaises(TypeError, dumps, [b('\xa4')],
                              encoding=None)
            self.assertEqual(dumps([b('\xa4')], encoding=None,
                                        default=decode_iso_8859_15),
                             r'["\u20ac"]')
        else:
            self.assertEqual(dumps([b('\xe2\x82\xac')], encoding=None),
                             r'["\u20ac"]')
            self.assertRaises(UnicodeDecodeError, dumps, [b('\xa4')],
                              encoding=None)
            self.assertRaises(UnicodeDecodeError, dumps, [b('\xa4')],
                              encoding=None, default=decode_iso_8859_15)

    def test_bytes_key_5(self):
        self.assertEqual(dumps({b('\xe2\x82\xac'): 42}), r'{"\u20ac": 42}')
        self.assertRaises(UnicodeDecodeError, dumps, {b('\xa4'): 42})
        self.assertEqual(dumps({b('\xa4'): 42}, encoding='iso-8859-1'),
                         r'{"\u00a4": 42}')
        self.assertEqual(dumps({b('\xa4'): 42}, encoding='iso-8859-15'),
                         r'{"\u20ac": 42}')
        if PY3:
            self.assertRaises(TypeError, dumps, {b('\xe2\x82\xac'): 42},
                              encoding=None)
            self.assertRaises(TypeError, dumps, {b('\xa4'): 42},
                              encoding=None)
            self.assertRaises(TypeError, dumps, {b('\xa4'): 42},
                              encoding=None, default=decode_iso_8859_15)
            self.assertEqual(dumps({b('\xa4'): 42}, encoding=None,
                                        skipkeys=True),
                             r'{}')
        else:
            self.assertEqual(dumps({b('\xe2\x82\xac'): 42}, encoding=None),
                             r'{"\u20ac": 42}')
            self.assertRaises(UnicodeDecodeError, dumps, {b('\xa4'): 42},
                              encoding=None)
            self.assertRaises(UnicodeDecodeError, dumps, {b('\xa4'): 42},
                              encoding=None, default=decode_iso_8859_15)
            self.assertRaises(UnicodeDecodeError, dumps, {b('\xa4'): 42},
                              encoding=None, skipkeys=True)

    def test_py_encode_basestring_ascii(self):
        self._test_encode_basestring_ascii(py_encode_basestring_ascii)

    def _test_encode_basestring_ascii(self, encode_basestring_ascii):
        CASES = [
            (u'/\\"\ucafe\ubabe\uab98\ufcde\ubcda\uef4a\x08\x0c\n\r\t`1~!@#$%^&*()_+-=[]{}|;:\',./<>?', '"/\\\\\\"\\ucafe\\ubabe\\uab98\\ufcde\\ubcda\\uef4a\\b\\f\\n\\r\\t`1~!@#$%^&*()_+-=[]{}|;:\',./<>?"'),
            (u'\u0123\u4567\u89ab\ucdef\uabcd\uef4a', '"\\u0123\\u4567\\u89ab\\ucdef\\uabcd\\uef4a"'),
            (u'controls', '"controls"'),
            (u'\x08\x0c\n\r\t', '"\\b\\f\\n\\r\\t"'),
            (u'{"object with 1 member":["array with 1 element"]}', '"{\\"object with 1 member\\":[\\"array with 1 element\\"]}"'),
            (u' s p a c e d ', '" s p a c e d "'),
            (u'\U0001d120', '"\\ud834\\udd20"'),
            (u'\u03b1\u03a9', '"\\u03b1\\u03a9"'),
            (b('\xce\xb1\xce\xa9'), '"\\u03b1\\u03a9"'),
            (u'\u03b1\u03a9', '"\\u03b1\\u03a9"'),
            (b('\xce\xb1\xce\xa9'), '"\\u03b1\\u03a9"'),
            (u'\u03b1\u03a9', '"\\u03b1\\u03a9"'),
            (u'\u03b1\u03a9', '"\\u03b1\\u03a9"'),
            (u"`1~!@#$%^&*()_+-={':[,]}|;.</>?", '"`1~!@#$%^&*()_+-={\':[,]}|;.</>?"'),
            (u'\x08\x0c\n\r\t', '"\\b\\f\\n\\r\\t"'),
            (u'\u0123\u4567\u89ab\ucdef\uabcd\uef4a', '"\\u0123\\u4567\\u89ab\\ucdef\\uabcd\\uef4a"'),
        ]

        fname = encode_basestring_ascii.__name__
        for input_string, expect in CASES:
            result = encode_basestring_ascii(input_string)
            #self.assertEqual(result, expect,
            #    '{0!r} != {1!r} for {2}({3!r})'.format(
            #        result, expect, fname, input_string))
            self.assertEqual(result, expect,
                '%r != %r for %s(%r)' % (result, expect, fname, input_string))

    def test_sorted_dict_6(self):
        items = [('one', 1), ('two', 2), ('three', 3), ('four', 4), ('five', 5)]
        s = dumps(dict(items), sort_keys=True)
        self.assertEqual(s, '{"five": 5, "four": 4, "one": 1, "three": 3, "two": 2}')

    def setUp(self):
        self.decoder = JSONDecoder()
        self.encoder = JSONEncoderForHTML()
        self.non_ascii_encoder = JSONEncoderForHTML(ensure_ascii=False)

    def test_basic_encode_7(self):
        self.assertEqual(r'"\u0026"', self.encoder.encode('&'))
        self.assertEqual(r'"\u003c"', self.encoder.encode('<'))
        self.assertEqual(r'"\u003e"', self.encoder.encode('>'))
        self.assertEqual(r'"\u2028"', self.encoder.encode(u'\u2028'))

    def test_non_ascii_basic_encode_7(self):
        self.assertEqual(r'"\u0026"', self.non_ascii_encoder.encode('&'))
        self.assertEqual(r'"\u003c"', self.non_ascii_encoder.encode('<'))
        self.assertEqual(r'"\u003e"', self.non_ascii_encoder.encode('>'))
        self.assertEqual(r'"\u2028"', self.non_ascii_encoder.encode(u'\u2028'))

    def test_basic_roundtrip_7(self):
        for char in '&<>':
            self.assertEqual(
                char, self.decoder.decode(
                    self.encoder.encode(char)))

    def test_prevent_script_breakout_7(self):
        bad_string = '</script><script>alert("gotcha")</script>'
        self.assertEqual(
            r'"\u003c/script\u003e\u003cscript\u003e'
            r'alert(\"gotcha\")\u003c/script\u003e"',
            self.encoder.encode(bad_string))
        self.assertEqual(
            bad_string, self.decoder.decode(
                self.encoder.encode(bad_string)))

    def test_string_keys_error_8(self):
        data = [{'a': 'A', 'b': (2, 4), 'c': 3.0, ('d',): 'D tuple'}]
        try:
            dumps(data)
        except TypeError:
            err = sys.exc_info()[1]
        else:
            self.fail('Expected TypeError')
        self.assertEqual(str(err),
                'keys must be str, int, float, bool or None, not tuple')

    def test_decode_error_8(self):
        err = None
        try:
            loads('{}\na\nb')
        except JSONDecodeError:
            err = sys.exc_info()[1]
        else:
            self.fail('Expected JSONDecodeError')
        self.assertEqual(err.lineno, 2)
        self.assertEqual(err.colno, 1)
        self.assertEqual(err.endlineno, 3)
        self.assertEqual(err.endcolno, 2)

    def test_scan_error_8(self):
        err = None
        for t in (text_type, b):
            try:
                loads(t('{"asdf": "'))
            except JSONDecodeError:
                err = sys.exc_info()[1]
            else:
                self.fail('Expected JSONDecodeError')
            self.assertEqual(err.lineno, 1)
            self.assertEqual(err.colno, 10)

    def test_error_is_pickable_8(self):
        err = None
        try:
            loads('{}\na\nb')
        except JSONDecodeError:
            err = sys.exc_info()[1]
        else:
            self.fail('Expected JSONDecodeError')
        s = pickle.dumps(err)
        e = pickle.loads(s)

        self.assertEqual(err.msg, e.msg)
        self.assertEqual(err.doc, e.doc)
        self.assertEqual(err.pos, e.pos)
        self.assertEqual(err.end, e.end)

    def test_failures_9(self):
        for idx, doc in enumerate(JSONDOCS):
            idx = idx + 1
            if idx in SKIPS:
                loads(doc)
                continue
            try:
                loads(doc)
            except JSONDecodeError:
                pass
            else:
                self.fail("Expected failure for fail%d.json: %r" % (idx, doc))

    def test_array_decoder_issue46_9(self):
        # http://code.google.com/p/simplejson/issues/detail?id=46
        for doc in [u'[,]', '[,]']:
            try:
                loads(doc)
            except JSONDecodeError:
                e = sys.exc_info()[1]
                self.assertEqual(e.pos, 1)
                self.assertEqual(e.lineno, 1)
                self.assertEqual(e.colno, 2)
            except Exception:
                e = sys.exc_info()[1]
                self.fail("Unexpected exception raised %r %s" % (e, e))
            else:
                self.fail("Unexpected success parsing '[,]'")

    def test_truncated_input_9(self):
        test_cases = [
            ('', 'Expecting value', 0),
            ('[', "Expecting value or ']'", 1),
            ('[42', "Expecting ',' delimiter", 3),
            ('[42,', 'Expecting value', 4),
            ('["', 'Unterminated string starting at', 1),
            ('["spam', 'Unterminated string starting at', 1),
            ('["spam"', "Expecting ',' delimiter", 7),
            ('["spam",', 'Expecting value', 8),
            ('{', 'Expecting property name enclosed in double quotes', 1),
            ('{"', 'Unterminated string starting at', 1),
            ('{"spam', 'Unterminated string starting at', 1),
            ('{"spam"', "Expecting ':' delimiter", 7),
            ('{"spam":', 'Expecting value', 8),
            ('{"spam":42', "Expecting ',' delimiter", 10),
            ('{"spam":42,', 'Expecting property name enclosed in double quotes',
             11),
            ('"', 'Unterminated string starting at', 0),
            ('"spam', 'Unterminated string starting at', 0),
            ('[,', "Expecting value", 1),
        ]
        for data, msg, idx in test_cases:
            try:
                loads(data)
            except JSONDecodeError:
                e = sys.exc_info()[1]
                self.assertEqual(
                    e.msg[:len(msg)],
                    msg,
                    "%r doesn't start with %r for %r" % (e.msg, msg, data))
                self.assertEqual(
                    e.pos, idx,
                    "pos %r != %r for %r" % (e.pos, idx, data))
            except Exception:
                e = sys.exc_info()[1]
                self.fail("Unexpected exception raised %r %s" % (e, e))
            else:
                self.fail("Unexpected success parsing '%r'" % (data,))

    def test_degenerates_allow_10(self):
        for inf in (PosInf, NegInf):
            self.assertEqual(loads(dumps(inf)), inf)
        # Python 2.5 doesn't have math.isnan
        nan = loads(dumps(NaN))
        self.assertTrue((0 + nan) != nan)

    def test_degenerates_ignore_10(self):
        for f in (PosInf, NegInf, NaN):
            self.assertEqual(loads(dumps(f, ignore_nan=True)), None)

    def test_degenerates_deny_10(self):
        for f in (PosInf, NegInf, NaN):
            self.assertRaises(ValueError, dumps, f, allow_nan=False)

    def test_floats_10(self):
        for num in [1617161771.7650001, math.pi, math.pi**100,
                    math.pi**-100, 3.1]:
            self.assertEqual(float(dumps(num)), num)
            self.assertEqual(loads(dumps(num)), num)
            self.assertEqual(loads(text_type(dumps(num))), num)

    def test_ints_10(self):
        for num in [1, long_type(1), 1<<32, 1<<64]:
            self.assertEqual(dumps(num), str(num))
            self.assertEqual(int(dumps(num)), num)
            self.assertEqual(loads(dumps(num)), num)
            self.assertEqual(loads(text_type(dumps(num))), num)

    def assertRoundTrip(self, obj, other, for_json=True):
        if for_json is None:
            # None will use the default
            s = dumps(obj)
        else:
            s = dumps(obj, for_json=for_json)
        self.assertEqual(
            loads(s),
            other)

    def test_for_json_encodes_stand_alone_object_11(self):
        self.assertRoundTrip(
            ForJson(),
            ForJson().for_json())

    def test_for_json_encodes_object_nested_in_dict_11(self):
        self.assertRoundTrip(
            {'hooray': ForJson()},
            {'hooray': ForJson().for_json()})

    def test_for_json_encodes_object_nested_in_list_within_dict_11(self):
        self.assertRoundTrip(
            {'list': [0, ForJson(), 2, 3]},
            {'list': [0, ForJson().for_json(), 2, 3]})

    def test_for_json_encodes_object_nested_within_object_11(self):
        self.assertRoundTrip(
            NestedForJson(),
            {'nested': {'for_json': 1}})

    def test_for_json_encodes_list_11(self):
        self.assertRoundTrip(
            ForJsonList(),
            ForJsonList().for_json())

    def test_for_json_encodes_list_within_object_11(self):
        self.assertRoundTrip(
            {'nested': ForJsonList()},
            {'nested': ForJsonList().for_json()})

    def test_for_json_encodes_dict_subclass_11(self):
        self.assertRoundTrip(
            DictForJson(a=1),
            DictForJson(a=1).for_json())

    def test_for_json_encodes_list_subclass_11(self):
        self.assertRoundTrip(
            ListForJson(['l']),
            ListForJson(['l']).for_json())

    def test_for_json_ignored_if_not_true_with_dict_subclass_11(self):
        for for_json in (None, False):
            self.assertRoundTrip(
                DictForJson(a=1),
                {'a': 1},
                for_json=for_json)

    def test_for_json_ignored_if_not_true_with_list_subclass_11(self):
        for for_json in (None, False):
            self.assertRoundTrip(
                ListForJson(['l']),
                ['l'],
                for_json=for_json)

    def test_raises_typeerror_if_for_json_not_true_with_object_11(self):
        self.assertRaises(TypeError, dumps, ForJson())
        self.assertRaises(TypeError, dumps, ForJson(), for_json=False)

    def test_indent_12(self):
        h = [['blorpie'], ['whoops'], [], 'd-shtaeou', 'd-nthiouh',
             'i-vhbjkhnth',
             {'nifty': 87}, {'field': 'yes', 'morefield': False} ]

        expect = textwrap.dedent("""\
        [
        \t[
        \t\t"blorpie"
        \t],
        \t[
        \t\t"whoops"
        \t],
        \t[],
        \t"d-shtaeou",
        \t"d-nthiouh",
        \t"i-vhbjkhnth",
        \t{
        \t\t"nifty": 87
        \t},
        \t{
        \t\t"field": "yes",
        \t\t"morefield": false
        \t}
        ]""")


        d1 = dumps(h)
        d2 = dumps(h, indent='\t', sort_keys=True, separators=(',', ': '))
        d3 = dumps(h, indent='  ', sort_keys=True, separators=(',', ': '))
        d4 = dumps(h, indent=2, sort_keys=True, separators=(',', ': '))

        h1 = loads(d1)
        h2 = loads(d2)
        h3 = loads(d3)
        h4 = loads(d4)

        self.assertEqual(h1, h)
        self.assertEqual(h2, h)
        self.assertEqual(h3, h)
        self.assertEqual(h4, h)
        self.assertEqual(d3, expect.replace('\t', '  '))
        self.assertEqual(d4, expect.replace('\t', '  '))
        # NOTE: Python 2.4 textwrap.dedent converts tabs to spaces,
        #       so the following is expected to fail. Python 2.4 is not a
        #       supported platform in simplejson 2.1.0+.
        self.assertEqual(d2, expect)

    def test_indent0_12(self):
        h = {3: 1}
        def check(indent, expected):
            d1 = dumps(h, indent=indent)
            self.assertEqual(d1, expected)

            sio = StringIO()
            dump(h, sio, indent=indent)
            self.assertEqual(sio.getvalue(), expected)

        # indent=0 should emit newlines
        check(0, '{\n"3": 1\n}')
        # indent=None is more compact
        check(None, '{"3": 1}')

    def test_separators_12(self):
        lst = [1,2,3,4]
        expect = '[\n1,\n2,\n3,\n4\n]'
        expect_spaces = '[\n1, \n2, \n3, \n4\n]'
        # Ensure that separators still works
        self.assertEqual(
            expect_spaces,
            dumps(lst, indent=0, separators=(', ', ': ')))
        # Force the new defaults
        self.assertEqual(
            expect,
            dumps(lst, indent=0, separators=(',', ': ')))
        # Added in 2.1.4
        self.assertEqual(
            expect,
            dumps(lst, indent=0))

    def test_simple_first_13(self):
        a = {'a': 1, 'c': 5, 'jack': 'jill', 'pick': 'axe', 'array': [1, 5, 6, 9], 'tuple': (83, 12, 3), 'crate': 'dog', 'zeak': 'oh'}
        self.assertEqual(
            '{"a": 1, "c": 5, "crate": "dog", "jack": "jill", "pick": "axe", "zeak": "oh", "array": [1, 5, 6, 9], "tuple": [83, 12, 3]}',
            dumps(a, item_sort_key=simple_first))

    def test_case_13(self):
        a = {'a': 1, 'c': 5, 'Jack': 'jill', 'pick': 'axe', 'Array': [1, 5, 6, 9], 'tuple': (83, 12, 3), 'crate': 'dog', 'zeak': 'oh'}
        self.assertEqual(
            '{"Array": [1, 5, 6, 9], "Jack": "jill", "a": 1, "c": 5, "crate": "dog", "pick": "axe", "tuple": [83, 12, 3], "zeak": "oh"}',
            dumps(a, item_sort_key=itemgetter(0)))
        self.assertEqual(
            '{"a": 1, "Array": [1, 5, 6, 9], "c": 5, "crate": "dog", "Jack": "jill", "pick": "axe", "tuple": [83, 12, 3], "zeak": "oh"}',
            dumps(a, item_sort_key=lambda kv: kv[0].lower()))

    def test_item_sort_key_value_13(self):
        # https://github.com/simplejson/simplejson/issues/173
        a = {'a': 1, 'b': 0}
        self.assertEqual(
            '{"b": 0, "a": 1}',
            dumps(a, item_sort_key=lambda kv: kv[1]))

    def test_namedtuple_dumps_14(self):
        for v in [Value(1), Point(1, 2), DuckValue(1), DuckPoint(1, 2)]:
            d = v._asdict()
            self.assertEqual(d, loads(dumps(v)))
            self.assertEqual(
                d,
                loads(dumps(v, namedtuple_as_object=True)))
            self.assertEqual(d, loads(dumps(v, tuple_as_array=False)))
            self.assertEqual(
                d,
                loads(dumps(v, namedtuple_as_object=True,
                                      tuple_as_array=False)))

    def test_namedtuple_dumps_false_14(self):
        for v in [Value(1), Point(1, 2)]:
            l = list(v)
            self.assertEqual(
                l,
                loads(dumps(v, namedtuple_as_object=False)))
            self.assertRaises(TypeError, dumps, v,
                tuple_as_array=False, namedtuple_as_object=False)

    def test_namedtuple_dump_14(self):
        for v in [Value(1), Point(1, 2), DuckValue(1), DuckPoint(1, 2)]:
            d = v._asdict()
            sio = StringIO()
            dump(v, sio)
            self.assertEqual(d, loads(sio.getvalue()))
            sio = StringIO()
            dump(v, sio, namedtuple_as_object=True)
            self.assertEqual(
                d,
                loads(sio.getvalue()))
            sio = StringIO()
            dump(v, sio, tuple_as_array=False)
            self.assertEqual(d, loads(sio.getvalue()))
            sio = StringIO()
            dump(v, sio, namedtuple_as_object=True,
                      tuple_as_array=False)
            self.assertEqual(
                d,
                loads(sio.getvalue()))

    def test_namedtuple_dump_false_14(self):
        for v in [Value(1), Point(1, 2)]:
            l = list(v)
            sio = StringIO()
            dump(v, sio, namedtuple_as_object=False)
            self.assertEqual(
                l,
                loads(sio.getvalue()))
            self.assertRaises(TypeError, dump, v, StringIO(),
                tuple_as_array=False, namedtuple_as_object=False)

    def test_asdict_not_callable_dump_14(self):
        for f in CONSTRUCTORS:
            self.assertRaises(TypeError,
                dump, f(DeadDuck()), StringIO(), namedtuple_as_object=True)
            sio = StringIO()
            dump(f(DeadDict()), sio, namedtuple_as_object=True)
            self.assertEqual(
                dumps(f({})),
                sio.getvalue())

    def test_asdict_not_callable_dumps_14(self):
        for f in CONSTRUCTORS:
            self.assertRaises(TypeError,
                dumps, f(DeadDuck()), namedtuple_as_object=True)
            self.assertEqual(
                dumps(f({})),
                dumps(f(DeadDict()), namedtuple_as_object=True))

    def test_parse_15(self):
        # test in/out equivalence and parsing
        res = loads(JSON1)
        out = dumps(res)
        self.assertEqual(res, loads(out))

    def test_parse_16(self):
        # test in/out equivalence and parsing
        res = loads(JSON2)
        out = dumps(res)
        self.assertEqual(res, loads(out))

    def test_parse_17(self):
        # test in/out equivalence and parsing
        res = loads(JSON3)
        out = dumps(res)
        self.assertEqual(res, loads(out))

    def test_normal_str_18(self):
        dct1, dct2, dct3, dct4 = _dicts()
        self.assertNotEqual(dumps(dct2), dumps(dct3))

    def test_raw_json_str_18(self):
        dct1, dct2, dct3, dct4 = _dicts()
        self.assertEqual(dumps(dct2), dumps(dct4))
        self.assertEqual(dct2, loads(dumps(dct4)))

    def test_list_19(self):
        dct1, dct2, dct3, dct4 = _dicts()
        self.assertEqual(
            dumps([dct2]),
            dumps([RawJSON(dumps(dct2))]))
        self.assertEqual(
            [dct2],
            loads(dumps([RawJSON(dumps(dct2))])))

    def test_direct_19(self):
        dct1, dct2, dct3, dct4 = _dicts()
        self.assertEqual(
            dumps(dct2),
            dumps(RawJSON(dumps(dct2))))
        self.assertEqual(
            dct2,
            loads(dumps(RawJSON(dumps(dct2)))))

    def test_listrecursion_20(self):
        x = []
        x.append(x)
        try:
            dumps(x)
        except ValueError:
            pass
        else:
            self.fail("didn't raise ValueError on list recursion")
        x = []
        y = [x]
        x.append(y)
        try:
            dumps(x)
        except ValueError:
            pass
        else:
            self.fail("didn't raise ValueError on alternating list recursion")
        y = []
        x = [y, y]
        # ensure that the marker is cleared
        dumps(x)

    def test_dictrecursion_20(self):
        x = {}
        x["test"] = x
        try:
            dumps(x)
        except ValueError:
            pass
        else:
            self.fail("didn't raise ValueError on dict recursion")
        x = {}
        y = {"a": x, "b": x}
        # ensure that the marker is cleared
        dumps(y)

    def test_defaultrecursion_20(self):
        enc = RecursiveJSONEncoder()
        self.assertEqual(enc.encode(JSONTestObject), '"JSONTestObject"')
        enc.recurse = True
        try:
            enc.encode(JSONTestObject)
        except ValueError:
            pass
        else:
            self.fail("didn't raise ValueError on default recursion")

    # The bytes type is intentionally not used in most of these tests
    # under Python 3 because the decoder immediately coerces to str before
    # calling scanstring. In Python 2 we are testing the code paths
    # for both unicode and str.
    #
    # The reason this is done is because Python 3 would require
    # entirely different code paths for parsing bytes and str.
    #
    def test_py_scanstring(self):
        self._test_scanstring(py_scanstring)

    def _test_scanstring(self, scanstring):
        if sys.maxunicode == 65535:
            self.assertEqual(
                scanstring(u'"z\U0001d120x"', 1, None, True),
                (u'z\U0001d120x', 6))
        else:
            self.assertEqual(
                scanstring(u'"z\U0001d120x"', 1, None, True),
                (u'z\U0001d120x', 5))

        self.assertEqual(
            scanstring('"\\u007b"', 1, None, True),
            (u'{', 8))

        self.assertEqual(
            scanstring('"A JSON payload should be an object or array, not a string."', 1, None, True),
            (u'A JSON payload should be an object or array, not a string.', 60))

        self.assertEqual(
            scanstring('["Unclosed array"', 2, None, True),
            (u'Unclosed array', 17))

        self.assertEqual(
            scanstring('["extra comma",]', 2, None, True),
            (u'extra comma', 14))

        self.assertEqual(
            scanstring('["double extra comma",,]', 2, None, True),
            (u'double extra comma', 21))

        self.assertEqual(
            scanstring('["Comma after the close"],', 2, None, True),
            (u'Comma after the close', 24))

        self.assertEqual(
            scanstring('["Extra close"]]', 2, None, True),
            (u'Extra close', 14))

        self.assertEqual(
            scanstring('{"Extra comma": true,}', 2, None, True),
            (u'Extra comma', 14))

        self.assertEqual(
            scanstring('{"Extra value after close": true} "misplaced quoted value"', 2, None, True),
            (u'Extra value after close', 26))

        self.assertEqual(
            scanstring('{"Illegal expression": 1 + 2}', 2, None, True),
            (u'Illegal expression', 21))

        self.assertEqual(
            scanstring('{"Illegal invocation": alert()}', 2, None, True),
            (u'Illegal invocation', 21))

        self.assertEqual(
            scanstring('{"Numbers cannot have leading zeroes": 013}', 2, None, True),
            (u'Numbers cannot have leading zeroes', 37))

        self.assertEqual(
            scanstring('{"Numbers cannot be hex": 0x14}', 2, None, True),
            (u'Numbers cannot be hex', 24))

        self.assertEqual(
            scanstring('[[[[[[[[[[[[[[[[[[[["Too deep"]]]]]]]]]]]]]]]]]]]]', 21, None, True),
            (u'Too deep', 30))

        self.assertEqual(
            scanstring('{"Missing colon" null}', 2, None, True),
            (u'Missing colon', 16))

        self.assertEqual(
            scanstring('{"Double colon":: null}', 2, None, True),
            (u'Double colon', 15))

        self.assertEqual(
            scanstring('{"Comma instead of colon", null}', 2, None, True),
            (u'Comma instead of colon', 25))

        self.assertEqual(
            scanstring('["Colon instead of comma": false]', 2, None, True),
            (u'Colon instead of comma', 25))

        self.assertEqual(
            scanstring('["Bad value", truth]', 2, None, True),
            (u'Bad value', 12))

        for c in map(chr, range(0x00, 0x1f)):
            self.assertEqual(
                scanstring(c + '"', 0, None, False),
                (c, 2))
            self.assertRaises(
                ValueError,
                scanstring, c + '"', 0, None, True)

        self.assertRaises(ValueError, scanstring, '', 0, None, True)
        self.assertRaises(ValueError, scanstring, 'a', 0, None, True)
        self.assertRaises(ValueError, scanstring, '\\', 0, None, True)
        self.assertRaises(ValueError, scanstring, '\\u', 0, None, True)
        self.assertRaises(ValueError, scanstring, '\\u0', 0, None, True)
        self.assertRaises(ValueError, scanstring, '\\u01', 0, None, True)
        self.assertRaises(ValueError, scanstring, '\\u012', 0, None, True)
        self.assertRaises(ValueError, scanstring, '\\u0123', 0, None, True)
        if sys.maxunicode > 65535:
            self.assertRaises(ValueError,
                              scanstring, '\\ud834\\u"', 0, None, True)
            self.assertRaises(ValueError,
                              scanstring, '\\ud834\\x0123"', 0, None, True)

    def test_issue3623(self):
        self.assertRaises(ValueError, scanstring, "xxx", 1,
                          "xxx")
        self.assertRaises(UnicodeDecodeError,
                          encode_basestring_ascii, b("xx\xff"))

    def test_overflow(self):
        # Python 2.5 does not have maxsize, Python 3 does not have maxint
        maxsize = getattr(sys, 'maxsize', getattr(sys, 'maxint', None))
        assert maxsize is not None
        self.assertRaises(OverflowError, scanstring, "xxx",
                          maxsize + 1)

    def test_surrogates(self):

        def assertScan(given, expect, test_utf8=True):
            givens = [given]
            if not PY3 and test_utf8:
                givens.append(given.encode('utf8'))
            for given in givens:
                (res, count) = scanstring(given, 1, None, True)
                self.assertEqual(len(given), count)
                self.assertEqual(res, expect)

        assertScan(
            u'"z\\ud834\\u0079x"',
            u'z\ud834yx')
        assertScan(
            u'"z\\ud834\\udd20x"',
            u'z\U0001d120x')
        assertScan(
            u'"z\\ud834\\ud834\\udd20x"',
            u'z\ud834\U0001d120x')
        assertScan(
            u'"z\\ud834x"',
            u'z\ud834x')
        assertScan(
            u'"z\\udd20x"',
            u'z\udd20x')
        assertScan(
            u'"z\ud834x"',
            u'z\ud834x')
        # It may look strange to join strings together, but Python is drunk.
        # https://gist.github.com/etrepum/5538443
        assertScan(
            u'"z\\ud834\udd20x12345"',
            u''.join([u'z\ud834', u'\udd20x12345']))
        assertScan(
            u'"z\ud834\\udd20x"',
            u''.join([u'z\ud834', u'\udd20x']))
        # these have different behavior given UTF8 input, because the surrogate
        # pair may be joined (in maxunicode > 65535 builds)
        assertScan(
            u''.join([u'"z\ud834', u'\udd20x"']),
            u''.join([u'z\ud834', u'\udd20x']),
            test_utf8=False)

        self.assertRaises(ValueError,
                          scanstring, u'"z\\ud83x"', 1, None, True)
        self.assertRaises(ValueError,
                          scanstring, u'"z\\ud834\\udd2x"', 1, None, True)

    def test_separators_22(self):
        h = [['blorpie'], ['whoops'], [], 'd-shtaeou', 'd-nthiouh', 'i-vhbjkhnth',
             {'nifty': 87}, {'field': 'yes', 'morefield': False} ]

        expect = textwrap.dedent("""\
        [
          [
            "blorpie"
          ] ,
          [
            "whoops"
          ] ,
          [] ,
          "d-shtaeou" ,
          "d-nthiouh" ,
          "i-vhbjkhnth" ,
          {
            "nifty" : 87
          } ,
          {
            "field" : "yes" ,
            "morefield" : false
          }
        ]""")


        d1 = dumps(h)
        d2 = dumps(h, indent='  ', sort_keys=True, separators=(' ,', ' : '))

        h1 = loads(d1)
        h2 = loads(d2)

        self.assertEqual(h1, h)
        self.assertEqual(h2, h)
        self.assertEqual(d2, expect)

    def test_dump_load_23(self):
        for s in ['', '"hello"', 'text', u'\u005c']:
            self.assertEqual(
                s,
                loads(dumps(WonkyTextSubclass(s))))

            self.assertEqual(
                s,
                loads(dumps(WonkyTextSubclass(s),
                                                  ensure_ascii=False)))

    def test_int_24(self):
        self.assertEqual(dumps(AlternateInt(1)), '1')
        self.assertEqual(dumps(AlternateInt(-1)), '-1')
        self.assertEqual(loads(dumps({AlternateInt(1): 1})), {'1': 1})

    def test_float_24(self):
        self.assertEqual(dumps(AlternateFloat(1.0)), '1.0')
        self.assertEqual(dumps(AlternateFloat(-1.0)), '-1.0')
        self.assertEqual(loads(dumps({AlternateFloat(1.0): 1})), {'1.0': 1})

    def test_tuple_array_dumps_25(self):
        t = (1, 2, 3)
        expect = dumps(list(t))
        # Default is True
        self.assertEqual(expect, dumps(t))
        self.assertEqual(expect, dumps(t, tuple_as_array=True))
        self.assertRaises(TypeError, dumps, t, tuple_as_array=False)
        # Ensure that the "default" does not get called
        self.assertEqual(expect, dumps(t, default=repr))
        self.assertEqual(expect, dumps(t, tuple_as_array=True,
                                            default=repr))
        # Ensure that the "default" gets called
        self.assertEqual(
            dumps(repr(t)),
            dumps(t, tuple_as_array=False, default=repr))

    def test_tuple_array_dump_25(self):
        t = (1, 2, 3)
        expect = dumps(list(t))
        # Default is True
        sio = StringIO()
        dump(t, sio)
        self.assertEqual(expect, sio.getvalue())
        sio = StringIO()
        dump(t, sio, tuple_as_array=True)
        self.assertEqual(expect, sio.getvalue())
        self.assertRaises(TypeError, dump, t, StringIO(),
                          tuple_as_array=False)
        # Ensure that the "default" does not get called
        sio = StringIO()
        dump(t, sio, default=repr)
        self.assertEqual(expect, sio.getvalue())
        sio = StringIO()
        dump(t, sio, tuple_as_array=True, default=repr)
        self.assertEqual(expect, sio.getvalue())
        # Ensure that the "default" gets called
        sio = StringIO()
        dump(t, sio, tuple_as_array=False, default=repr)
        self.assertEqual(
            dumps(repr(t)),
            sio.getvalue())

    def test_encoding1_26(self):
        encoder = JSONEncoder(encoding='utf-8')
        u = u'\N{GREEK SMALL LETTER ALPHA}\N{GREEK CAPITAL LETTER OMEGA}'
        s = u.encode('utf-8')
        ju = encoder.encode(u)
        js = encoder.encode(s)
        self.assertEqual(ju, js)

    def test_encoding2_26(self):
        u = u'\N{GREEK SMALL LETTER ALPHA}\N{GREEK CAPITAL LETTER OMEGA}'
        s = u.encode('utf-8')
        ju = dumps(u, encoding='utf-8')
        js = dumps(s, encoding='utf-8')
        self.assertEqual(ju, js)

    def test_encoding3_26(self):
        u = u'\N{GREEK SMALL LETTER ALPHA}\N{GREEK CAPITAL LETTER OMEGA}'
        j = dumps(u)
        self.assertEqual(j, '"\\u03b1\\u03a9"')

    def test_encoding4_26(self):
        u = u'\N{GREEK SMALL LETTER ALPHA}\N{GREEK CAPITAL LETTER OMEGA}'
        j = dumps([u])
        self.assertEqual(j, '["\\u03b1\\u03a9"]')

    def test_encoding5_26(self):
        u = u'\N{GREEK SMALL LETTER ALPHA}\N{GREEK CAPITAL LETTER OMEGA}'
        j = dumps(u, ensure_ascii=False)
        self.assertEqual(j, u'"' + u + u'"')

    def test_encoding6_26(self):
        u = u'\N{GREEK SMALL LETTER ALPHA}\N{GREEK CAPITAL LETTER OMEGA}'
        j = dumps([u], ensure_ascii=False)
        self.assertEqual(j, u'["' + u + u'"]')

    def test_big_unicode_encode_26(self):
        u = u'\U0001d120'
        self.assertEqual(dumps(u), '"\\ud834\\udd20"')
        self.assertEqual(dumps(u, ensure_ascii=False), u'"\U0001d120"')

    def test_big_unicode_decode_26(self):
        u = u'z\U0001d120x'
        self.assertEqual(loads('"' + u + '"'), u)
        self.assertEqual(loads('"z\\ud834\\udd20x"'), u)

    def test_unicode_decode_26(self):
        for i in range(0, 0xd7ff):
            u = unichr(i)
            #s = '"\\u{0:04x}"'.format(i)
            s = '"\\u%04x"' % (i,)
            self.assertEqual(loads(s), u)

    def test_object_pairs_hook_with_unicode_26(self):
        s = u'{"xkd":1, "kcw":2, "art":3, "hxm":4, "qrt":5, "pad":6, "hoy":7}'
        p = [(u"xkd", 1), (u"kcw", 2), (u"art", 3), (u"hxm", 4),
             (u"qrt", 5), (u"pad", 6), (u"hoy", 7)]
        self.assertEqual(loads(s), eval(s))
        self.assertEqual(loads(s, object_pairs_hook=lambda x: x), p)
        od = loads(s, object_pairs_hook=OrderedDict)
        self.assertEqual(od, OrderedDict(p))
        self.assertEqual(type(od), OrderedDict)
        # the object_pairs_hook takes priority over the object_hook
        self.assertEqual(loads(s,
                                    object_pairs_hook=OrderedDict,
                                    object_hook=lambda x: None),
                         OrderedDict(p))


    def test_default_encoding_26(self):
        self.assertEqual(loads(u'{"a": "\xe9"}'.encode('utf-8')),
            {'a': u'\xe9'})

    def test_unicode_preservation_26(self):
        self.assertEqual(type(loads(u'""')), text_type)
        self.assertEqual(type(loads(u'"a"')), text_type)
        self.assertEqual(type(loads(u'["a"]')[0]), text_type)

    def test_ensure_ascii_false_returns_unicode_26(self):
        # http://code.google.com/p/simplejson/issues/detail?id=48
        self.assertEqual(type(dumps([], ensure_ascii=False)), text_type)
        self.assertEqual(type(dumps(0, ensure_ascii=False)), text_type)
        self.assertEqual(type(dumps({}, ensure_ascii=False)), text_type)
        self.assertEqual(type(dumps("", ensure_ascii=False)), text_type)

    def test_ensure_ascii_false_bytestring_encoding_26(self):
        # http://code.google.com/p/simplejson/issues/detail?id=48
        doc1 = {u'quux': b('Arr\xc3\xaat sur images')}
        doc2 = {u'quux': u'Arr\xeat sur images'}
        doc_ascii = '{"quux": "Arr\\u00eat sur images"}'
        doc_unicode = u'{"quux": "Arr\xeat sur images"}'
        self.assertEqual(dumps(doc1), doc_ascii)
        self.assertEqual(dumps(doc2), doc_ascii)
        self.assertEqual(dumps(doc1, ensure_ascii=False), doc_unicode)
        self.assertEqual(dumps(doc2, ensure_ascii=False), doc_unicode)

    def test_ensure_ascii_linebreak_encoding_26(self):
        # http://timelessrepo.com/json-isnt-a-javascript-subset
        s1 = u'\u2029\u2028'
        s2 = s1.encode('utf8')
        expect = '"\\u2029\\u2028"'
        expect_non_ascii = u'"\u2029\u2028"'
        self.assertEqual(dumps(s1), expect)
        self.assertEqual(dumps(s2), expect)
        self.assertEqual(dumps(s1, ensure_ascii=False), expect_non_ascii)
        self.assertEqual(dumps(s2, ensure_ascii=False), expect_non_ascii)

    def test_invalid_escape_sequences_26(self):
        # incomplete escape sequence
        self.assertRaises(JSONDecodeError, loads, '"\\u')
        self.assertRaises(JSONDecodeError, loads, '"\\u1')
        self.assertRaises(JSONDecodeError, loads, '"\\u12')
        self.assertRaises(JSONDecodeError, loads, '"\\u123')
        self.assertRaises(JSONDecodeError, loads, '"\\u1234')
        # invalid escape sequence
        self.assertRaises(JSONDecodeError, loads, '"\\u123x"')
        self.assertRaises(JSONDecodeError, loads, '"\\u12x4"')
        self.assertRaises(JSONDecodeError, loads, '"\\u1x34"')
        self.assertRaises(JSONDecodeError, loads, '"\\ux234"')
        if sys.maxunicode > 65535:
            # invalid escape sequence for low surrogate
            self.assertRaises(JSONDecodeError, loads, '"\\ud800\\u"')
            self.assertRaises(JSONDecodeError, loads, '"\\ud800\\u0"')
            self.assertRaises(JSONDecodeError, loads, '"\\ud800\\u00"')
            self.assertRaises(JSONDecodeError, loads, '"\\ud800\\u000"')
            self.assertRaises(JSONDecodeError, loads, '"\\ud800\\u000x"')
            self.assertRaises(JSONDecodeError, loads, '"\\ud800\\u00x0"')
            self.assertRaises(JSONDecodeError, loads, '"\\ud800\\u0x00"')
            self.assertRaises(JSONDecodeError, loads, '"\\ud800\\ux000"')

    def test_ensure_ascii_still_works_26(self):
        # in the ascii range, ensure that everything is the same
        for c in map(unichr, range(0, 127)):
            self.assertEqual(
                dumps(c, ensure_ascii=False),
                dumps(c))
        snowman = u'\N{SNOWMAN}'
        self.assertEqual(
            dumps(c, ensure_ascii=False),
            '"' + c + '"')

    def test_strip_bom_26(self):
        content = u"\u3053\u3093\u306b\u3061\u308f"
        json_doc = codecs.BOM_UTF8 + b(dumps(content))
        self.assertEqual(load(BytesIO(json_doc)), content)
        for doc in json_doc, json_doc.decode('utf8'):
            self.assertEqual(loads(doc), content)