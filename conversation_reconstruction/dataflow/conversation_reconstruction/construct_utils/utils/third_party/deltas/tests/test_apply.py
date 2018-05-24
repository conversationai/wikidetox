from nose.tools import eq_

from ..apply import apply
from ..operations import Insert, Equal, Delete


def test_apply():
    a = [0,1,2,3,4,5,6]
    b = [0,1,2,3,"four", "five", "six", "seven", "eight", "nine", 6]
    replayed_b = list(apply([Insert(0, 0, 0, 4), Delete(4, 6, 4, 4),
                             Insert(4, 4, 4, 10), Equal(6, 7, 10, 11)],
                             a, b))
    eq_(b, replayed_b)
