# -*- coding: utf-8 -*-
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

A dataflow pipeline to collect statistics on Wikipedia talk pages including number of revisions and their sizes.

Run with:

  python dataflow_metadata.py --input [YourIngestedFiles] --output [IntendedOutputStorage] --setup_file ./setup.py
         [Optional] --testmode (runnning locally for test)

"""
from __future__ import absolute_import
import argparse
import logging
import traceback
import subprocess
import resource
import json
from os import path
import urllib2
import ast
import copy
import sys

import apache_beam as beam
from apache_beam.io import filesystems
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import SetupOptions
from construct_utils.conversation_constructor import Conversation_Constructor


def get_metadata(x):
  record_size = len(x)
  record = json.loads(x)
  return json.dumps({'page_id': record['page_id'], 'rev_id': record['rev_id'],
                     'timestamp': record['timestamp'], 'record_size': record_size})


def run(known_args, pipeline_args):
  """Main entry point; defines and runs the reconstruction pipeline."""

  if known_args.testmode:
    pipeline_args.append('--runner=DirectRunner')
  else:
    pipeline_args.append('--runner=DataflowRunner')
  pipeline_args.extend([
    '--project=wikidetox-viz',
    '--staging_location=gs://wikidetox-viz-dataflow/staging',
    '--temp_location=gs://wikidetox-viz-dataflow/tmp',
    '--job_name=get-metadata',
    '--max_num_workers=80'
  ])
  pipeline_options = PipelineOptions(pipeline_args)
  pipeline_options.view_as(SetupOptions).save_main_session = True

  with beam.Pipeline(options=pipeline_options) as p:
    p = (p | 'Read_to_be_processed' >> beam.io.ReadFromText(known_args.input)
         | 'Map_to_meatadata' >> beam.Map(lambda x : get_metadata(x))
         | 'WriteToFile' >> beam.io.WriteToText(known_args.output))


if __name__ == '__main__':
  logging.basicConfig(filename="debug.log", level=logging.INFO)
  logging.getLogger().setLevel(logging.INFO)
  parser = argparse.ArgumentParser()
  # input/output parameters.
  parser.add_argument('--input',
                      dest='input',
                      help='input storage.')
  parser.add_argument('--output',
                      dest='output',
                      help='The output directory')
  parser.add_argument('--testmode',
                      dest='testmode',
                      action='store_true',
                      help='Whether to run in testmode.')
  known_args, pipeline_args = parser.parse_known_args()
  run(known_args, pipeline_args)

