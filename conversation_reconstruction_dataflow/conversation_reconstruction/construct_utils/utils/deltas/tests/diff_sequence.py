from nose.tools import eq_

from ..apply import apply
from ..tokenizers import text_split


def diff_sequence(process, tokenizer=None):
    revisions = ["This sentence is a sentence.  This is gonna go.",
                 "This sentence is a sentence.  Hi!  I'm new here.",
                 "Hi!  I'm new here.  This sentence is a sentence. ",
                 "I'm new here.  This sentence is a sentence. I'm new here.",
                 "I'm new here. Sentence is a sentence."]

    token_operations = process(revisions)

    tokens = []
    for ops, a, b in token_operations:
        tokens = apply(ops, a, b)
        print("|".join(str(t) for t in b))


    eq_(''.join(tokens), revisions[-1])
