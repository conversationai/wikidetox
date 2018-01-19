from ...tests.diff_and_replay import diff_and_replay
from ...tests.diff_sequence import diff_sequence
from ..sequence_matcher import diff, process
from ...tokenizers import text_split


def test_diff_and_replay():
    return diff_and_replay(diff)


def test_engine():
    return diff_sequence(process)
