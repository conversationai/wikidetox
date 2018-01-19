from nose.tools import eq_

from ..apply import apply
from ..tokenizers import text_split


def diff_and_replay(diff):
    a = """
    This sentence is going to get copied. This sentence is going to go away.

    This is a paragraph that is mostly going to change.  However, there's going
    to be a sentence right in the middle that stays.  And now we're done with
    that.

    This is another sentence. asldknasl dsal dals dals dlasd oa kdlawbndkubawdk
    """

    b = """
    This sentence is going to get copied.  Wha... a new thing appeared!

    Everyone thought that this paragraph would totally change.  However, there's
    going to be a sentence right in the middle that stays.  Isn't that funny!?

    This is another sentence. This sentence is going to get copied.
    """
    a_tokens = list(text_split.tokenize(a))
    b_tokens = list(text_split.tokenize(b))
    operations = list(diff(a_tokens, b_tokens))

    print("Diff 1:")
    for op in operations:
        if op.name == "equal":
            print("equal: " + repr("".join(a_tokens[op.a1:op.a2])))
        elif op.name == "delete":
            print("delete: " + repr("".join(a_tokens[op.a1:op.a2])))
        elif op.name == "insert":
            print("insert: " + repr("".join(b_tokens[op.b1:op.b2])))

    replay_b = [str(t) for t in apply(operations, a_tokens, b_tokens)]
    eq_(b, ''.join(replay_b))


    a = "I'm new here.  This sentence is a sentence. I'm new here."
    b = "I'm new here. Sentence is a sentence."

    a_tokens = list(text_split.tokenize(a))
    b_tokens = list(text_split.tokenize(b))
    operations = list(diff(a_tokens, b_tokens))

    print("\nDiff 2:")
    for op in operations:
        if op.name == "equal":
            print("equal: " + repr("".join(a_tokens[op.a1:op.a2])))
        elif op.name == "delete":
            print("delete: " + repr("".join(a_tokens[op.a1:op.a2])))
        elif op.name == "insert":
            print("insert: " + repr("".join(b_tokens[op.b1:op.b2])))

    replay_b = [str(t) for t in apply(operations, a_tokens, b_tokens)]
    eq_(b, ''.join(replay_b))

    a = """This is a test paragraph.  It has some sentences.

    I have a lovely bunch of coconuts.

    This is another test paragraph.  It also has some sentences.

    This is a test sentence just floating in space."""

    b = """This is a test paragraph.  It has some sentences.

    This is another test paragraph.  It also has some sentences.

    I have a lovely bunch of coconuts.

    This is a test sentence just floating in space."""

    a_tokens = list(text_split.tokenize(a))
    b_tokens = list(text_split.tokenize(b))
    operations = list(diff(a_tokens, b_tokens))

    print("\nDiff 3:")
    for op in operations:
        if op.name == "equal":
            print("equal: " + repr("".join(a_tokens[op.a1:op.a2])))
        elif op.name == "delete":
            print("delete: " + repr("".join(a_tokens[op.a1:op.a2])))
        elif op.name == "insert":
            print("insert: " + repr("".join(b_tokens[op.b1:op.b2])))

    replay_b = [str(t) for t in apply(operations, a_tokens, b_tokens)]
    eq_(b, ''.join(replay_b))
