"""Copyright 2017 Google Inc. Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.

You may obtain a copy of the License at
    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

-------------------------------------------------------------------------------

Ingester Test

A unit test for wikipedia_revisions_ingester.py and run_ingester.py

Run with  python -m ingest_utils.ingester_test
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import unittest
import json
import xml.sax
import os
import signal
import sys
import copy
import time
from io import BytesIO

from wikiconv.ingest_revisions.ingest_utils import wikipedia_revisions_ingester as wiki_ingester
import resource
import math
import os
test_length = 10000
text_length = 10000
memory_boundary = 40000  #in KB
time_limit = 2  #seconds


def generateInfiniteXML(length, w):
  with open(
      os.path.join(os.environ["TEST_SRCDIR"],
                   '__main__/wikiconv/ingest_revisions/testdata/mediawiki_header.xml'), 'r') as f:
    mediawiki_header = ''
    for line in f:
      mediawiki_header = mediawiki_header + line
  non_talk_page_header = ('<page>\n<title>This is not a talk '
                          'page</title>\n<ns>6</ns>\n<id>111111</id>\n')
  cnt = 0
  text = 'x' * text_length
  w.write(mediawiki_header)
  for cnt in range(length):
    content = '<revision>\n<id>{id}</id>\n<text>{text}</text>\n</revision>\n'.format(
        id=cnt, text=text)
    w.write(content)
  w.write('</page>\n')
  w.write(non_talk_page_header)
  text = text * 5
  for cnt in range(length):
    content = '<revision>\n<id>{id}</id>\n<text>{text}</text>\n</revision>\n'.format(
        id=cnt, text=text)
    w.write(content)
  w.write('</page>\n</mediawiki>')


class TestWikiIngester(unittest.TestCase):

  def test_ingester(self):
    input_file = os.path.join(os.environ["TEST_SRCDIR"],
        '__main__/wikiconv/ingest_revisions/testdata', 'test_wiki_dump.xml')
    for i, line in enumerate(wiki_ingester.parse_stream(input_file)):
      if i == 0:
        self.assertEqual(line['comment'], 'a test comment 1')
        self.assertEqual(line['user_text'], '111.111.111.111')
        self.assertEqual(line['user_id'], None)
      if i == 1:
        self.assertEqual(line['page_title'], 'Third Page (namespace 1)')
        self.assertEqual(
            line['text'],
            ' The first revision on the third page. Written by Tinker JJ. Has a comment.'
        )
      if i == 2 or i == 3:
        self.assertEqual(line['page_id'], '54197571')
    # The fourth revision includes a large text component.
    self.assertEqual(i, 4)

    # This is a test on parsing very large xml files to make sure the streaming
    # doesn't consume too much memory.
    gigantic = os.path.join(os.environ['TEST_TMPDIR'], 'gigantic_xml.xml')
    with open(gigantic, 'w') as w:
      generateInfiniteXML(test_length, w)
    input_file = gigantic
    start = time.time()
    for i, line in enumerate(wiki_ingester.parse_stream(input_file)):
      if i % 5000 == 0:
        memory_usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        self.assertLessEqual(memory_usage, memory_boundary)
    costed_time = time.time() - start
    self.assertLessEqual(costed_time, time_limit)
    print('Time spent on parsing: ', costed_time)


if __name__ == '__main__':
  unittest.main()
