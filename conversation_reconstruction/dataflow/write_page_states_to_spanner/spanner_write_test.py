"""Tests for spanner_write."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import unittest
from write_utils.write import SpannerWriter 
from google.gax import retry


class SpannerWriteTest(unittest.TestCase):

  def test_spanner_write(self):
    writer = SpannerWriter('wikiconv', 'page_info')
    writer.create_table('page_states', ('page_id', 'authors',
                                       'conversation_id', 'deleted_comments',
                                       'page_state', 'rev_id', 'timestamp'))
    try:
       ret = writer.insert_data('page_states', [('test_page_id', 'test_authors', 'test_conversation_id',
                                  'test_deleted_comments', 'test_page_state', 123,
                                  '2018-06-29T00:00:00Z')])
    except Exception as e:
      if 'StatusCode.ALREADY_EXISTS' in str(e):
        ret = 'Inserted data.'
        pass
      else:
        raise Exception(e)
    self.assertEqual(ret, 'Inserted data.')
    try:
       ret = writer.insert_data('page_states', [('test_page_id', 'test_authors', 'test_conversation_id',
                                  'test_deleted_comments', 'test_page_state', 124,
                                  '2018-06-29T00:00:00Z')])
    except Exception as e:
      if 'StatusCode.ALREADY_EXISTS' in str(e):
        ret = 'Inserted data.'
        pass
      else:
        raise Exception(e)

    self.assertEqual(ret, 'Inserted data.')
    pass


if __name__ == '__main__':
  unittest.main()
