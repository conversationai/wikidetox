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
import dataflow_main


class DataflowTest(unittest.TestCase):

  def test_index_by_page_id(self):
    data = '{"page_id": "deadbeef", "content": "Abracadabra"}'
    actual = dataflow_main.index_by_page_id(data)
    self.assertTupleEqual(('deadbeef', {
        'page_id': 'deadbeef',
        'content': 'Abracadabra'
    }), actual)

  def test_index_by_rev_id(self):
    data = '{"rev_id": "deadbeef", "content": "Abracadabra"}'
    actual = dataflow_main.index_by_rev_id(data)
    self.assertTupleEqual(('deadbeef', data), actual)

  def test_mark_revisions_of_big_pages(self):
    pipeline = test_pipeline.TestPipeline()
    pc = beam.Create([('page_1', [{
        'record_size': 100,
        'rev_id': 'rev1-a'
    }, {
        'record_size': dataflow_main.CUMULATIVE_REVISION_SIZE_THERESHOLD,
        'rev_id': 'rev1-b'
    }]),
                      ('page_2', [{
                          'record_size': 100,
                          'rev_id': 'rev2-a'
                      }, {
                          'record_size': 100,
                          'rev_id': 'rev2-b'
                      }])])
    res = pipeline | pc | beam.ParDo(dataflow_main.MarkRevisionsOfBigPages())
    util.assert_that(
        res,
        util.equal_to([('rev1-a', 1), ('rev1-b', 1), ('rev2-a', 0),
                       ('rev2-b', 0)]))
    pipeline.run()

  def test_write_to_storage(self):
    tempdir = tempfile.mkdtemp()
    os.mkdir(os.path.join(tempdir, 'yyy'))
    pipeline = test_pipeline.TestPipeline()
    pc = beam.Create([
        ('rev_1', {
            'metadata': [dataflow_main.SAVE_TO_MEMORY],
            'raw': [
                '{"page_id":"xxx","rev_id":"13","timestamp":1558015201059}'
            ]
        }),
        ('rev_2', {
            'metadata': [dataflow_main.SAVE_TO_STORAGE],
            'raw': [
                '{"page_id":"yyy","rev_id":"26","timestamp":1558015201100}'
            ]
        }),
    ])
    res = pipeline | pc | beam.ParDo(dataflow_main.WriteToStorage(), tempdir)
    util.assert_that(
        res,
        util.equal_to([(u'xxx', {
            u'timestamp': 1558015201059,
            u'page_id': u'xxx',
            u'rev_id': 13
        }), (u'yyy', {
            'timestamp': 1558015201100,
            'rev_id': 26
        })]))
    pipeline.run()
    with open(os.path.join(tempdir, 'yyy', '26')) as f:
      self.assertEqual(
          f.read(),
          '{"timestamp": 1558015201100, "page_id": "yyy", "rev_id": "26"}')
    shutil.rmtree(tempdir)


if __name__ == '__main__':
  unittest.main()
