from nose.tools import eq_

from ...apply import apply
from ...operations import Delete, Equal, Insert
from ...tests.diff_and_replay import diff_and_replay
from ...tests.diff_sequence import diff_sequence
from ...tokenizers import text_split, wikitext_split
from ..segment_matcher import diff, process


def test_diff_and_replay():
    return diff_and_replay(diff)


def test_engine():
    return diff_sequence(process)


def test_easy_diff():
    a = "Apples are red."
    b = "Apples are tasty and red."

    operation_tokens = process([a, b], tokenizer=wikitext_split)

    # Apples are red.
    operations, a, b = next(operation_tokens)

    # Apples are tasty and red.
    operations, a, b = next(operation_tokens)

    eq_(
        list(operations),
        [
            Equal(0, 4, 0, 4),
            Insert(4, 4, 4, 8),
            Equal(4, 6, 8, 10)
        ]
    )


def test_sentence_sandwich():
    a = """==Senior Tours==

Golfers over the age of fifty are eligible to compete in senior touraments.
[[Golf]] is unique among [[sports]] in having high profile and lucrative
competitions for this age group. Nearly all of the famous golfers who are
eligible to compete in these events choose to do so these events, unless
they are unable to for health reasons. The two main tours are:

*[[Champions Tour]] (based in the [[United States]]}
*[[European Seniors Tour]]"""

    b = """==Senior Tours==

Golfers over the age of fifty are eligible to compete in senior touraments.
[[Golf]] is unique among [[sports]] in having high profile and lucrative
competitions for this age group. Nearly all of the famous golfers who are
eligible to compete in these events choose to do so, unless
they are unable to for health reasons. The two main tours are:

*[[Champions Tour]] (based in the [[United States]]}
*[[European Seniors Tour]]"""

    operation_tokens = process([a, a, b], tokenizer=wikitext_split)

    operations, a, b = next(operation_tokens)

    operations, a, b = next(operation_tokens)
    
    operations, a, b = next(operation_tokens)

    eq_(
        list(operations),
        [Equal(name='equal', a1=0, a2=105, b1=0, b2=105),
         Delete(name='delete', a1=105, a2=109, b1=105, b2=105),
         Equal(name='equal', a1=109, a2=168, b1=105, b2=164)]
    )
