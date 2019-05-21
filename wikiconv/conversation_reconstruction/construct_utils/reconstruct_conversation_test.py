"""Tests for ReconstructConversation."""

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

  def test_reconstruct_conversation_empty_test(self):
    storage_mock = FakeStorageClient()
    tempdir = tempfile.mkdtemp()

    pipeline = test_pipeline.TestPipeline()
    pc = beam.Create([(None, {}),
                      ('page1', {
                          'last_revision': [],
                          'page_state': [],
                          'error_log': [],
                          'to_be_processed': []
                      }),
                      ('page2', {
                          'last_revision': ['xxx'],
                          'page_state': [{
                              'page_state': {
                                  'actions': {}
                              },
                              'authors': {}
                          }],
                          'error_log': [],
                          'to_be_processed': []
                      }),
                      ('page3', {
                          'last_revision': ['yyy'],
                          'page_state': [{
                              'page_state': {
                                  'actions': {}
                              },
                              'authors': {}
                          }],
                          'error_log': [],
                          'to_be_processed': []
                      }),
                      ])
    res = pipeline | pc | beam.ParDo(
        reconstruct_conversation.ReconstructConversation(storage_mock),
        tempdir).with_outputs(
            'page_states',
            'last_revision',
            'error_log',
            main='reconstruction_results')
    util.assert_that(
        res['page_states'],
        util.equal_to([
            '{"page_state": {"actions": {}}, "authors": {}}',
            '{"page_state": {"actions": {}}, "authors": {}}'
                       ]),
        label='page_states')
    util.assert_that(
        res['last_revision'], util.equal_to(['"xxx"', '"yyy"']), label='last_revision')
    util.assert_that(res['error_log'], util.equal_to([]), label='error_log')
    util.assert_that(
        res['reconstruction_results'],
        util.equal_to([]),
        label='reconstruction')
    pipeline.run()
    shutil.rmtree(tempdir)


if __name__ == '__main__':
  unittest.main()
