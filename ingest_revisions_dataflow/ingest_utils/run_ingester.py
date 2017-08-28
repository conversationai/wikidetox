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

Runs wikipedia_revisions_ingester.py with command line arguments for input.

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import xml.sax
import subprocess
import argparse
from os import path
from ingest_utils import wikipedia_revisions_ingester

parser = argparse.ArgumentParser(description='Download and save wikipedia revisions from a dump.')
parser.add_argument('-i', '--input', required = True, help='Path to a wikipedia xml or 7z revision dump file.')

args = parser.parse_args()

def run(input_file):
	wikipedia_revisions_ingester.parse_stream(input_file)


if __name__ == '__main__':
	run(args.input)