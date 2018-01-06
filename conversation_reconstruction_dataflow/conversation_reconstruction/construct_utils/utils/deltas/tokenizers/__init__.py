"""
Tokenizers are used to split text content into a sequence of tokens.  Extend
:class:`~deltas.Tokenizer` to implement a custom tokenizer.  See
also :class:`~deltas.RegexTokenizer` for producing a tokenizer
based on a lexicon.

**deltas.text_split**
    a :class:`~deltas.RegexTokenizer` that splits text into words,
    punctuation, symbols and whitespace.

**deltas.wikitext_split**
    a :class:`~deltas.RegexTokenizer` that splits text into words,
    punctuation, symbols and whitespace as well as wikitext markup elements
    (e.g. ('dcurly_open', "{{") and ('bold', "'''"))
"""
from .tokenizer import Tokenizer, RegexTokenizer
from .token import Token
from .text_split import text_split
from .wikitext_split import wikitext_split
