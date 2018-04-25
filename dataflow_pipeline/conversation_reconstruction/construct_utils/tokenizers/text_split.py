from .tokenizer import RegexTokenizer

LEXICON = [
    ('word',          r'[^\W\d]+'),
    ('number',        r'[\d]+'),
    ('period',        r'[\.]+'),
    ('qmark',         r'\?'),
    ('epoint',        r'!'),
    ('comma',         r','),
    ('colon',         r':'),
    ('scolon',        r';'),
    ('break',         r'\n'),
    ('whitespace',    r'[\r\s]'),
    ("etc",           r".")
]

text_split = RegexTokenizer(LEXICON)
