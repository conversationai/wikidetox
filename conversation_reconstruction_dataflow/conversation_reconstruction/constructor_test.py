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
import os
import signal
import sys
import copy

from threading import Timer
from os import path
import math
THERESHOLD = 500

class TestWikiConstructor(unittest.TestCase):
  def test_ingester(self):
    input_file = path.join('construct_utils', 'testdata', 'test_revisions_list.json')
    with open(input_file) as f:
         input_data = json.load(f)
    construction_cmd = ['python2', '-m', 'construct_utils.run_constructor', '--table', input_data['table'], '--revisions', json.dumps(input_data['revisions'])]
    construct_proc = subprocess.Popen(construction_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize = 4096)
    for i, line in enumerate(construct_proc.stdout):
        try:
           output = json.loads(line)
           print(output)   
        except:
           print(line)

if __name__ == '__main__':
  unittest.main()
