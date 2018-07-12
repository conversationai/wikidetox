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
Run Processor
Runs process.py with command line arguments for input.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import json
from os import path
from ingest_utils import process

parser = argparse.ArgumentParser(description='Ouputs sentence-level diff of two revisions.')
parser.add_argument('-i', '--input', required = True, help='The name file that stores the revision pair in json format.')

args = parser.parse_args()

def run(input_file):
  with open(input_file, "r") as f:
    (former, current) = json.load(f)
  ret = process.process_pair(former, current)
  print(json.dumps(ret))


if __name__ == '__main__':
  run(args.input)

