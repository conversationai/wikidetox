"""
Sequence Matcher
----------------

Performs a simple *longest-common-substring* diff.  This module implements a
simple wrapper around :class:`difflib.SequenceMatcher`.

.. autofunction:: deltas.algorithms.sequence_matcher.diff

.. autofunction:: deltas.algorithms.sequence_matcher.process

.. autoclass:: deltas.SequenceMatcher
    :members:
"""

from difflib import SequenceMatcher as SM

from ..operations import Delete, Equal, Insert
from ..tokenizers import Token, text_split
from .diff_engine import DiffEngine

TOKENIZER = text_split

OP_PARSERS = {
    "replace": lambda a1, a2, b1, b2: [Delete(a1, a2, b1, b1),
                                       Insert(a2, a2, b1, b2)],
    "insert": lambda a1, a2, b1, b2: [Insert(a1, a2, b1, b2)],
    "delete": lambda a1, a2, b1, b2: [Delete(a1, a2, b1, b2)],
    "equal": lambda a1, a2, b1, b2: [Equal(a1, a2, b1, b2)]
}


def diff(a, b):
    """
    Performs a longest common substring diff.

    :Parameters:
        a : sequence of `comparable`
            Initial sequence
        b : sequence of `comparable`
            Changed sequence

    :Returns:
        An `iterable` of operations.
    """
    a, b = list(a), list(b)
    opcodes = SM(None, a, b).get_opcodes()
    return parse_opcodes(opcodes)


def process(texts, *args, **kwargs):
    processor = SequenceMatcher.Processor(*args, **kwargs)

    for text in texts:
        yield processor.process(text)


class SequenceMatcher(DiffEngine):
    """
    Constructs a sequence matching diff engine that preserves verion state
    and is able to process changes sequentially.  When detecting changes
    across many versions of a text this strategy will be about twice as fast as
    calling :func:`diff` sequentially.

    :Example:
        >>> from deltas.algorithms import SequenceMatcher
        >>> engine = SequenceMatcher()
        >>>
        >>> processor = engine.processor()
        >>> ops, a, b = processor.process("This is a version.  It has some " +
        ...                               "text in it.")
        >>> print(" ".join(repr(''.join(b[op.b1:op.b2])) for op in ops))
        'This is a version.  It has some text in it.'
        >>> ops, a, b = processor.process("This is a version.  However, it " +
        ...                               "has different.")
        >>> print(" ".join(repr(''.join(b[op.b1:op.b2])) for op in ops))
        'This is a version.  ' '' 'However, it' ' has ' '' 'different' '.'
        >>> ops, a, b = processor.process("Switching it up here.  This is " +
        ...                               "a version.")
        >>> print(" ".join(repr(''.join(b[op.b1:op.b2])) for op in ops))
        'Switching it up here.  ' 'This is a version.' ''
    """

    class Processor(DiffEngine.Processor):
        __slots__ = ('last_tokens')
        """
        A processor used by the SequenceMatcher difference engine to track the
        history of a single text.
        """
        def __init__(self, tokenizer=None, last_text=None, last_tokens=None,
                     token_class=None):
            self.tokenizer = tokenizer or TOKENIZER
            self.update(last_text, last_tokens)
            self.token_class = token_class

        def update(self, last_text=None, last_tokens=None, **kwargs):
            if last_text is not None:
                self.last_tokens = self.tokenizer.tokenize(last_text, **kwargs)
            else:
                self.last_tokens = last_tokens or []

        def process(self, text, token_class=None):
            """
            Processes a new version of a text and returns the delta.

            :Parameters:
                text : `str`
                    The text to process

            :Returns:
                A tuple of `operations`, `a_tokens`, `b_tokens`
            """
            token_class = token_class or self.token_class
            tokens = self.tokenizer.tokenize(text, token_class=token_class)
            operations = diff(self.last_tokens, tokens)

            a = self.last_tokens
            b = tokens
            self.last_tokens = tokens

            return operations, a, b

    def __init__(self, tokenizer=None):
        self.tokenizer = tokenizer or TOKENIZER

    def processor(self, *args, **kwargs):
        return self.Processor(self.tokenizer, *args, **kwargs)

    def process(self, texts, *args, **kwargs):
        return process(texts, self.tokenizer, *args, **kwargs)

    @classmethod
    def from_config(cls, config, name, section_key="diff_engines"):
        return cls()


def parse_opcodes(opcodes):

    for opcode in opcodes:
        op, a_start, a_end, b_start, b_end = opcode

        parse = OP_PARSERS[op]
        for operation in parse(a_start, a_end, b_start, b_end):
            yield operation
