"""Tests for wikiwatcher."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import sys

import unittest
from antidox import wikiwatcher

if sys.version_info >= (3, 3):
  from unittest import mock  # pylint: disable=g-import-not-at-top,g-importing-member
else:
  import mock  # pylint: disable=g-import-not-at-top,unused-import


class FakeEvent(object):

  def __init__(self, json_string):
    self.event = 'message'
    self.data = json_string


class WikiWatcherTest(unittest.TestCase):

  def test_wikiwatcher(self):
    events = [
        FakeEvent('{"wiki":"enwiki","bot":false,"title":"Yep!","namespace":1}'),
        FakeEvent('{"wiki":"frwiki","bot":false,"title":"Non!","namespace":0}'),
        FakeEvent('{"wiki":"enwiki","bot":true,"title":"Nope","namespace":0}'),
        FakeEvent('{"wiki":"enwiki","bot":true,"title":"Nope","namespace":1}')
    ]
    callback = mock.Mock()
    wikiwatcher.watcher(events, 'enwiki', set([1, 3]), callback)
    callback.assert_called_with({
        u'wiki': u'enwiki',
        u'namespace': 1,
        u'bot': False,
        u'title': u'Yep!'
    })


if __name__ == '__main__':
  unittest.main()
