from .tokenizer import RegexTokenizer

LEXICON = [
    ('word',          r'[^\W\d]+'),
    ('number',        r'[\d]+'),
    ('period',        r'\.'),
    ('qmark',         r'\?'),
    ('epoint',        r'!'),
    ('comma',         r','),
    ('colon',         r':'),
    ('scolon',        r';'),
    ('break',         r'(\n|\n\r|\r\n)\s*(\n|\n\r|\r\n)+'),
    ('whitespace',    r'[\n\r\s]+'),
    ("etc",           r".")
]

text_split = RegexTokenizer(LEXICON)
