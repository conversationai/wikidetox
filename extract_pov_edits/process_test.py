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
import resource
from threading import Timer
import signal


MEMLIMIT = 1024 * 1024 * 1024
my_timeout = 2

def set_memory_limit(soft, hard):
  resource.setrlimit(resource.RLIMIT_AS, (soft, hard))

class TestWikiIngester(unittest.TestCase):
  #def test_normal_revs(self):
  #  input_file = path.join('ingest_utils', 'testdata', 'dummy_test.json')
  #  ans_file = path.join('ingest_utils', 'testdata', 'dummy_test_ans.json')
  #  cur_sents = {}
  #  anses = []
  #  with open(input_file, 'r') as f:
  #    for i, line in enumerate(f):
  #        content = json.loads(line)
  #        ans, error = process(content, cur_sents)
  #        anses.append(ans)
  #  with open(ans_file, 'r') as f:
  #    standard = f.read()
  #  self.assertEqual(json.dumps(anses), standard)

  #def test_large_revs(self):
  #  content = {'rev_id': 'placeholder'}
  #  content['text'] = 'w' * 500000 + '. Haha there\'s a sentence.'
  #  start_time = time.time()
  #  ans, error = process(content, {})
  #  end_time = time.time()
  #  self.assertLess(end_time - start_time, 1)
  #  self.assertEqual(error, True)
  #  self.assertEqual(len(ans[1]), 1)

  def test_normal_rev_pair(self):
    input_file = path.join('ingest_utils', 'testdata', 'dummy_test.json')
    ans_file = path.join('ingest_utils', 'testdata', 'dummy_test_ans_pairs.json')
    anses = []
    with open(input_file, 'r') as f:
      former = None
      for i, line in enumerate(f):
        content = json.loads(line)
        tf = tempfile.NamedTemporaryFile(delete=False)
        json.dump((former, content), tf)
        tf.close()
        kill = lambda process, status: process.kill(); status='timeout'
        process_cmd = ['python2', '-m', 'ingest_utils.run_processor', '-i', tf.name]
        try:
          sub_proc = subprocess.Popen(process_cmd, stdout=subprocess.PIPE, preexec_fn=set_memory_limit(MEMLIMIT, -1))
          timer = Timer(my_timeout, kill, (sub_proc, status))
          timer.start()
        except MemoryError:
          pass
        else:
          stdout, stderr = sub_proc.communicate()
          sub_proc.wait()
          timer.cancel()
          set_memory_limit(-1, -1)
          ans = json.loads(stdout)
          anses.append([sorted(a) for a in ans])
        former = content
    with open(ans_file, 'r') as f:
      standard = f.read()
    self.assertEqual(json.dumps(anses), standard)

  def test_large_rev_pairs(self):
    content = {'rev_id': 'placeholder'}
    content['text'] = 'w' * 500000
    former = None
    start_time = time.time()

    tf = tempfile.NamedTemporaryFile(delete=False)
    json.dump((former, content), tf)
    tf.close()
    process_cmd = ['python2', '-m', 'ingest_utils.run_processor', '-i', tf.name]
    try:
      sub_proc = subprocess.Popen(process_cmd, stdout=subprocess.PIPE, preexec_fn=set_memory_limit(MEMLIMIT, -1))
    except MemoryError:
      pass
    else:
      timer = Timer(my_timeout, sub_proc.kill())
      timer.start()
      stdout, stderr = sub_proc.communicate()
      sub_proc.wait()
      timer.cancel()
      set_memory_limit(-1, -1)
    end_time = time.time()
    self.assertLess(end_time - start_time, 5)
    self.assertEqual(stdout, '')

if __name__ == '__main__':
  unittest.main()
