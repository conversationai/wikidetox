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

A dataflow pipeline to clean MediaWiki formats in comments and convert nested
array type to acceptable type in BigQuery.

Run with:

   python dataflow_content_clean.py --setup_file ./setup.py --input=InputStorage\
   --output=OutputStorage --jobname=YourJobName --project=YourCloudProject\
   --bucket=YourCloudBucket

"""
from __future__ import absolute_import
import argparse
import logging
import subprocess
import json
from os import path
import urllib2
import traceback
import sys
import multiprocessing
from construct_utils.utils.third_party.clean import content_clean

import apache_beam as beam
from apache_beam.metrics.metric import Metrics
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import SetupOptions

TIMEOUT = 2

def page_indexed_metadata_of_action(action):
  record = json.loads(action)
  return (record['page_id'], {'id': record['id'], 'page_id': record['page_id'], 'rev_id': record['rev_id'],
                              'timestamp': record['timestamp'], 'parent_id': record['parent_id'],
                              'ancestor_id': record['ancestor_id'], 'type': record['type']})



def run(known_args, pipeline_args):
  """Main entry point; defines and runs the sharding pipeline."""

  if known_args.testmode:
    pipeline_args.append('--runner=DirectRunner')
  else:
    pipeline_args.append('--runner=DataflowRunner')

  pipeline_args.extend([
      '--project={project}'.format(project=known_args.project),
      '--staging_location=gs://{bucket}/staging'.format(bucket=known_args.bucket),
      '--temp_location=gs://{bucket}/tmp'.format(bucket=known_args.bucket),
      '--job_name=postprocessing-{}'.format(known_args.jobname),
      '--num_workers=80'])
  pipeline_options = PipelineOptions(pipeline_args)
  pipeline_options.view_as(SetupOptions).save_main_session = True

  # Queries extracting the data
  with beam.Pipeline(options=pipeline_options) as p:
       results = (p | beam.io.ReadFromText(known_args.input)
               | 'mapToPageId' >> beam.Map(page_indexed_metadata_of_action)
               | beam.GroupByKey()
               | beam.ParDo(PostProcess()))
       results | "WriteResult" >> beam.io.WriteToText(known_args.output)

class PostProcess(beam.DoFn):
  def __init__(self):
    self.processed_records = Metrics.counter(self.__class__, 'processed_records')

  def process(self, element):
    """Convert nested array field to array; clean the wikipedia webpage format."""
    page_id, data = element
    data = sorted(data, key=lambda x: (x['timestamp'], int(x['rev_id'])))
    deletions = {}
    unchanged = {}
    for x in data:
      if x['ancestor_id'] is not None:
         unchanged[x['ancestor_id']] = x['type']
    for x in data:
      if (x['id'] in unchanged) and not(unchanged[x['id']] == 'RESTORATION'):
        x['isUnchanged'] = False
      else:
        x['isUnchanged'] = True 
      if x['type'] == 'DELETION':
         deletions[x['parent_id']] = x['id']
      if x['type'] == 'RESTORATION':
         x['parent_id'] = deletions[x['parent_id']]
      self.processed_records.inc()
      yield json.dumps(x)

if __name__ == '__main__':
  logging.getLogger().setLevel(logging.INFO)
  parser = argparse.ArgumentParser()
  # Input/Output parameters
  parser.add_argument('--project',
                      dest='project',
                      help='The cloud project.')
  parser.add_argument('--bucket',
                      dest='bucket',
                      help='The cloud bucket.')
  parser.add_argument('--input',
                      dest='input',
                      help='Input storage.')
  parser.add_argument('--output',
                      dest='output',
                      help='Output storage.')
  parser.add_argument('--jobname',
                      dest='jobname',
                      help='The dataflow jobname.')
  parser.add_argument('--testmode',
                      dest='testmode',
                      action='store_true',
                      help='Runs the dataflow pipeline using DirectRunner.')

  known_args, pipeline_args = parser.parse_known_args()
  run(known_args, pipeline_args)
