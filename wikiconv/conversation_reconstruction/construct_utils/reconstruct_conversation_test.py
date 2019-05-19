"""Tests for dataflow_main."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import shutil
import tempfile
import unittest

import apache_beam as beam
from apache_beam.testing import test_pipeline
from apache_beam.testing import util
from construct_utils import reconstruct_conversation

class FakeStorageClient(object):
  pass


class ReconstructConversationTest(unittest.TestCase):

  def test_reconstruct_conversation_empty_stub_test(self):
    storage_mock = FakeStorageClient()

    pipeline = test_pipeline.TestPipeline()
    pc = beam.Create([])
    res = pipeline | pc | beam.ParDo(reconstruct_conversation.ReconstructConversation(
        storage_mock))
    util.assert_that( res, util.equal_to([]))
    pipeline.run()


if __name__ == '__main__':
  unittest.main()
