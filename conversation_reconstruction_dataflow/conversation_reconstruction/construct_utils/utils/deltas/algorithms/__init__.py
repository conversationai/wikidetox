"""
The primary use-case of this library is to detect differences between two
sequences of tokens.  So far, two such algorithmic strategies are available:

:class:`~deltas.algorithms.sequence_matcher`
    implementes :func:`~deltas.algorithms.sequence_matcher.diff` that will
    compare two sequences of :class:`~deltas.Token` and return
    a set of operations.
:class:`~deltas.algorithms.segment_matcher`
    implementes :func:`~deltas.algorithms.segment_matcher.diff` that
    uses a :class:`~deltas.Segmenter` to detect block moves

Both of these algorithms are supplimented with a :class:`deltas.DiffEngine`
for efficiently processing several revisions of the same text

Implemented Algorithms
----------------------

Segment Matcher
+++++++++++++++
.. automodule:: deltas.algorithms.segment_matcher

Sequence Matcher
++++++++++++++++
.. automodule:: deltas.algorithms.sequence_matcher

Diff engine
-----------
.. automodule:: deltas.algorithms.diff_engine
"""

# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import (
         bytes, dict, int, list, object, range, str,
         ascii, chr, hex, input, next, oct, open,
         pow, round, super,
         filter, map, zip)
from .diff_engine import DiffEngine
from .sequence_matcher import SequenceMatcher
