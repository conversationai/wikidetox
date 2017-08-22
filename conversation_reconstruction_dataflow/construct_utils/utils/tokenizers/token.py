"""
Tokens represent chuncks of text that have semantic meaning.  A Token class that
extends :class:`str` is provided.

.. autoclass:: deltas.Token
    :members:
"""
from __future__ import absolute_import, division, print_function
from builtins import *
from future.builtins.disabled import *



class Token(str):
    """
    Constructs a typed sub-string extracted from a text.
    """

    def __new__(cls, content, *args, **kwargs):
        if isinstance(content, cls):
            return content
        else:
            return super().__new__(cls, content)

    def tokens(self):
        """
        Returns an iterator of *self*.  This method reflects the behavior of
        :meth:`deltas.Segment.tokens`
        """
        yield self

    def __init__(self, content, type=None):
        self.type = str(type) if type is not None else None
        """
        An optional value describing the type of token.
        """

    def __repr__(self):
        return "{0}({1}, type={2})" \
               .format(self.__class__.__name__,
                       super().__repr__(),
                       repr(self.type))
