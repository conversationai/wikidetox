from .tokenizer import RegexTokenizer

PLAIN_PROTO = [r'bitcoin', r'geo', r'magnet', r'mailto', r'news', r'sips?',
               r'tel', r'urn']
SLASHED_PROTO = [r'', r'ftp', r'ftps', r'git', r'gopher', r'https?', r'ircs?',
                 r'mms', r'nntp', r'redis', r'sftp', r'ssh', r'svn', r'telnet',
                 r'worldwind', r'xmpp']
ADDRESS = r'[^\s/$.?#].[^\s]*'

url = (
    r'(' +  # noqa
        r'(' + '|'.join(PLAIN_PROTO) + r')\:|' +  # noqa
        r'((' + '|'.join(SLASHED_PROTO) + r')\:)?\/\/' +
    r')' + ADDRESS
)
# re.compile(url, re.U).match("https://website.gov?param=value")

# Matches Chinese, Japanese and Korean characters.
cjk = (
    r'[' +
        r'\u4E00-\u62FF' +  # noqa Unified Ideographs
            r'\u6300-\u77FF' +
            r'\u7800-\u8CFF' +
            r'\u8D00-\u9FCC' +
        r'\u3400-\u4DFF' +  # Unified Ideographs Ext A
        r'\U00020000-\U000215FF' +  # Unified Ideographs Ext. B
            r'\U00021600-\U000230FF' +
            r'\U00023100-\U000245FF' +
            r'\U00024600-\U000260FF' +
            r'\U00026100-\U000275FF' +
            r'\U00027600-\U000290FF' +
            r'\U00029100-\U0002A6DF' +
        r'\uF900-\uFAFF' +  # Compatibility Ideographs
        r'\U0002F800-\U0002FA1F' +  # Compatibility Ideographs Suppl.
        r'\u3041-\u3096' +  # Hiragana
        r'\u30A0-\u30FF' +  # Katakana
        r'\u3400-\u4DB5' +  # Kanji
            r'\u4E00-\u9FCB' +
            r'\uF900-\uFA6A' +
        r'\u2E80-\u2FD5' +  # Kanji radicals
        r'\uFF5F-\uFF9F' +  # Katakana and Punctuation (Half Width)
        r'\u31F0-\u31FF' +  # Miscellaneous Japanese Symbols and Characters
            r'\u3220-\u3243' +
            r'\u3280-\u337F'
    r']'
)

devangari_word = r'\u0901-\u0963'
arabic_word = r'\u0601-\u061A' + \
              r'\u061C-\u0669' + \
              r'\u06D5-\u06EF'
bengali_word = r'\u0980-\u09FF'
combined_word = devangari_word + arabic_word + bengali_word

word = r'([^\W\d]|[' + combined_word + r'])' + \
       r'[\w' + combined_word + r']*' + \
       r'([\'’]([\w' + combined_word + r']+|(?=($|\s))))*'


LEXICON = [
    ('comment_start', r'<!--'),
    ('comment_end',   r'-->'),
    ("url",           url),
    ('entity',        r'&[a-z][a-z0-9]*;'),
    ('cjk',           cjk),
    ('ref_open',      r'<ref\b[^>/]*>'),
    ('ref_close',     r'</ref\b[^>]*>'),
    ('ref_singleton', r'<ref\b[^>/]*/>'),
    ('tag',           r'</?([a-z][a-z0-9]*)\b[^>]*>'),
    ('number',        r'[\d]+'),
    ('japan_punct',   r'[\u3000-\u303F]'),
    ('danda',         r'।|॥'),
    ("bold",          r"'''"),
    ("italic",        r"''"),
    ('word',          word),
    ('period',        r'\.+'),
    ('qmark',         r'\?+'),
    ('epoint',        r'!+'),
    ('comma',         r',+'),
    ('colon',         r':+'),
    ('scolon',        r';+'),
    ('break',         r'(\n|\n\r|\r\n)\s*(\n|\n\r|\r\n)+'),
    ('whitespace',    r'(\n|\n\r|[^\S\n\r]+)'),
    ('dbrack_open',   r'\[\['),
    ('dbrack_close',  r'\]\]'),
    ('brack_open',    r'\['),
    ('brack_close',   r'\]'),
    ('paren_open',    r'\('),
    ('paren_close',   r'\)'),
    ('tab_open',      r'\{\|'),
    ('tab_close',     r'\|\}'),
    ('dcurly_open',   r'\{\{'),
    ('dcurly_close',  r'\}\}'),
    ('curly_open',    r'\{'),
    ('curly_close',   r'\}'),
    ("equals",        r"=+"),
    ("bar",           r"\|"),
    ("etc",           r".")
]

wikitext_split = RegexTokenizer(LEXICON)
