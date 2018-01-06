"""
Apply operations
================
"""

from .operations import Delete, Equal, Insert


def apply(operations, a_tokens, b_tokens):
    """
    Applies a sequences of operations to tokens -- copies tokens from
    `a_tokens` and `b_tokens` according to `operations`.

    :Parameters:
        operations : sequence of :~class:`deltas.Operation`
            Operations to perform
        a_tokens : list of `comparable`
            Starting sequence of comparable tokens
        b_tokens : list of `comparable`
            Ending list of comparable tokens

    :Returns:
        A new list of tokens
    """
    for operation in operations:

        if isinstance(operation, Equal):
            #print("Equal: {0}".format(str(a_tokens[operation.a1:operation.a2])))
            for t in a_tokens[operation.a1:operation.a2]: yield t

        elif isinstance(operation, Insert):
            #print("Insert: {0}".format(str(b_tokens[operation.b1:operation.b2])))
            for t in b_tokens[operation.b1:operation.b2]: yield t

        elif isinstance(operation, Delete):
            #print("Delete: {0}".format(str(a_tokens[operation.a1:operation.a2])))
            pass

        else:
            raise TypeError("Unexpected operation type " + \
                            "{0}".format(type(operation)))
