"""
Copyright 2017 Google Inc.
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
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
import subprocess
from os import path
from ingest_utils import wikipedia_revisions_ingester as wiki_ingester

class TestWikiIngester(unittest.TestCase):

  def test_ingester(self):
    input_file = path.join('ingest_utils', 'testdata', 'test_wiki_dump.xml')
    ingestion_cmd = ['python2', '-m', 'ingest_utils.run_ingester', '-i', input_file]
    ingest_proc = subprocess.Popen(ingestion_cmd, stdout=subprocess.PIPE, bufsize = 4096)
    for i, line in enumerate(ingest_proc.stdout):
      parsed_line = json.loads(line)
      if i == 0:
        self.assertEqual(parsed_line['comment'], 'a test comment 1')
      if i == 1:
        self.assertEqual(parsed_line['page_title'], 'Third Page (namespace 1)')
      if i == 2 or i == 3:
        self.assertEqual(parsed_line['page_id'], '54197571')
    self.assertEqual(i, 3)


if __name__ == '__main__':
  unittest.main()
