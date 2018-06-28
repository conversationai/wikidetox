# -*- coding: utf-8 -*-
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

A dataflow pipeline to reconstruct conversations on Wikipedia talk pages from ingested json files.

Run with:

reconstruct*.sh in helper_shell

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


LOG_INTERVAL = 100
MENMORY_THERESHOLD = 1000000

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
    '--job_name=reshard-input',
    '--max_num_workers=80'
  ])
  pipeline_options = PipelineOptions(pipeline_args)
  pipeline_options.view_as(SetupOptions).save_main_session = True

  with beam.Pipeline(options=pipeline_options) as p:
    p = (p | 'Read_to_be_processed' >> beam.io.ReadFromText(known_args.input)
         | 'WriteToStorage' >> beam.ParDo(WriteToStorage(), known_args.outputdir)
         | 'WriteList' >> beam.io.WriteToText(known_args.outputlist))

class WriteToStorage(beam.DoFn):
  def process(self, element, outputdir):
      element = json.loads(element)
      page_id = element['page_id']
      rev_id = element['rev_id']
      # Creates writing path given the week, year pair
      write_path = path.join(outputdir, page_id, rev_id)
      # Writes to storage
      logging.info('USERLOG: Write to path %s.' % write_path)
      outputfile = filesystems.FileSystems.create(write_path)
      outputfile.write(json.dumps(element) + '\n')
      outputfile.close()
      yield json.dumps({'page_id': page_id, 'rev_id': int(rev_id)})


if __name__ == '__main__':
  logging.basicConfig(filename="debug.log", level=logging.INFO)
  logging.getLogger().setLevel(logging.INFO)
  parser = argparse.ArgumentParser()
  # input/output parameters.
  parser.add_argument('--input',
                      dest='input',
                      help='input storage.')
  parser.add_argument('--outputdir',
                      dest='outputdir',
                      default='gs://wikidetox-viz-dataflow/resharded-en-20180501/',
                      help='The output directory')
  parser.add_argument('--outputlist',
                      dest='outputlist',
                      default='gs://wikidetox-viz-dataflow/resharded-en-20180501/resharded-list.json',
                      help='The output directory')
  parser.add_argument('--testmode',
                      dest='testmode',
                      action='store_true',
                      help='Whether to run in testmode.')
  known_args, pipeline_args = parser.parse_known_args()
  run(known_args, pipeline_args)

