"""
Copyright 2018 Google Inc.
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

Process Test

A unit test for process.py.

Run with  python process_test
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import unittest
import json
import time
import subprocess
import tempfile
from os import path
from ingest_utils.process import process, process_pair, isSimilar
from dataflow_main import WriteDecompressedFile
import resource
from threading import Timer
import signal

class TestWikiIngester(unittest.TestCase):

  def test_normal_rev_pair(self):
    input_file = path.join('ingest_utils', 'testdata', 'dummy_test.json')
    ans_file = path.join('ingest_utils', 'testdata', 'dummy_test_ans_pairs.json')
    anses = []
    with open(input_file, 'r') as f:
      former = None
      for i, line in enumerate(f):
        content = json.loads(line)
        ans, err = WriteDecompressedFile.parse((former, content))
        if not(err):
          anses.append(json.loads(ans))
        former = content
    with open(ans_file, 'r') as f:
      standard = f.read()
    self.assertEqual(json.dumps(anses), standard)

  def test_large_rev_pairs(self):
    content = {'rev_id': 'placeholder'}
    content['text'] = 'w' * 500000
    former = None
    start_time = time.time()
    ans, err = WriteDecompressedFile.parse((former, content))
    end_time = time.time()
    self.assertLess(end_time - start_time, 5)
    self.assertEqual(ans, None)
    self.assertEqual(err, True)

if __name__ == '__main__':
  unittest.main()
