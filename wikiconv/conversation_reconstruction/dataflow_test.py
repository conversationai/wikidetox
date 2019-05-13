"""Tests for dataflow_main."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import dataflow_main
import unittest


class DataflowTest(unittest.TestCase):

  def test_index_by_page_id(self):
    data = '{"page_id": "deadbeef", "content": "Abracadabra"}'
    actual = dataflow_main.index_by_page_id(data)
    self.assertTupleEqual(
        ('deadbeef', {'page_id': 'deadbeef', 'content': 'Abracadabra'}),
        actual)


if __name__ == '__main__':
  unittest.main()
