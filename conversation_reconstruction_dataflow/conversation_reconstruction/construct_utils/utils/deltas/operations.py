"""
The delta between sequences of tokens is represented by a sequence of
:class:`~deltas.Operation`.  The goal of difference algorithms is to
detect a sequence of :class:`~deltas.Operation` that has desirable
properties.  :func:`~deltas.apply` can be used with a sequence of
:class:`~deltas.Operation` to convert an initial sequence of tokens
into a changed sequence of tokens.

Specifically, this library understands and produces three types of operations:

* :class:`~deltas.Delete` -- some tokens were deleted
* :class:`~deltas.Insert` -- some tokens were inserted
* :class:`~deltas.Equal` -- some tokens were copied

.. autoclass:: deltas.Delete
.. autoclass:: deltas.Insert
.. autoclass:: deltas.Equal

.. autoclass:: deltas.Operation
"""
from collections import namedtuple

Operation = namedtuple("Operation", ['name', 'a1', 'a2', 'b1', 'b2'])
"""
Represents an option performed on a sequence of tokens to arrive at another
sequence of tokens.  Instances of this type are compatible with the output of
:meth:`difflib.SequenceMatcher.get_opcodes`.
"""

""" This operation is useless and will be ignored
class Replace(Operation):
    def __init__(self, a1, a2, b1, b2):
        Operation.__init__(self, "replace", a1, a2, b1, b2)
"""


class Delete(Operation):
    """
    Represents the deletion of tokens.

    :Parameters:
        a1 : int
            Start position in first sequence.
        a2 : int
            End position in first sequence.
        b1 : int
            Start position in second sequence.
        b2 : int
            End position in second sequence.
    """

    OPNAME = "delete"

    def __new__(cls, a1, a2, b1, b2, name=None):
        return Operation.__new__(cls, "delete", a1, a2, b1, b2)

    def relevant_tokens(self, a, b):
        return a[self.a1:self.a2]


class Insert(Operation):
    """
    Represents the insertions of tokens.

    :Parameters:
        a1 : int
            Start position in first sequence.
        a2 : int
            End position in first sequence.
        b1 : int
            Start position in second sequence.
        b2 : int
            End position in second sequence.
    """

    OPNAME = "insert"

    def __new__(cls, a1, a2, b1, b2, name=None):
        return Operation.__new__(cls, "insert", a1, a2, b1, b2)

    def relevant_tokens(self, a, b):
        return b[self.b1:self.b2]


class Equal(Operation):
    """
    Represents the equality of tokens between sequences.

    :Parameters:
        a1 : int
            Start position in first sequence.
        a2 : int
            End position in first sequence.
        b1 : int
            Start position in second sequence.
        b2 : int
            End position in second sequence.
    """

    OPNAME = "equal"

    def __new__(cls, a1, a2, b1, b2, name=None):
        return Operation.__new__(cls, "equal", a1, a2, b1, b2)

    def relevant_tokens(self, a, b):
        return a[self.a1:self.a2]


def print_operations(operations, a, b):
    for operation in operations:
        print("{0}: '{1}'".format(operation.name,
                                  ''.join(operation.relevant_tokens(a, b))))
