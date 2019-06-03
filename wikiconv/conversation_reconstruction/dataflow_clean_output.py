# -*- coding: utf-8 -*-
"""Copyright 2018 Google Inc. Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.

You may obtain a copy of the License at
    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

-------------------------------------------------------------------------------

A dataflow pipeline to clean outputs scored by Perspective API internally,
replacing
':' in fields by '_'.

Run with:

"  python dataflow_clean_output.py --setup_file ./setup.py --input=InputStorage
--output=OutputStorage
   --project=YourCloudProject --bucket=YourCloudBucket"

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
from wikiconv.conversation_reconstruction.construct_utils.utils.third_party.clean import content_clean

import apache_beam as beam
from apache_beam.metrics.metric import Metrics
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import SetupOptions


def run(known_args, pipeline_args):
  """Main entry point; defines and runs the pipeline."""

  if known_args.testmode:
    pipeline_args.append('--runner=DirectRunner')
  else:
    pipeline_args.append('--runner=DataflowRunner')

  pipeline_args.extend([
      '--project={project}'.format(project=known_args.project),
      '--staging_location=gs://{bucket}/staging'.format(
          bucket=known_args.bucket),
      '--temp_location=gs://{bucket}/tmp'.format(bucket=known_args.bucket),
      '--job_name=scoring-formatting', '--num_workers=80'
  ])
  pipeline_options = PipelineOptions(pipeline_args)
  pipeline_options.view_as(SetupOptions).save_main_session = True

  # Queries extracting the data
  with beam.Pipeline(options=pipeline_options) as p:
    p = (
        p | beam.io.ReadFromText(known_args.input)
        | beam.ParDo(FieldNameFormatCleanForBigQuery())
        | 'WriteResult' >> beam.io.WriteToText(known_args.output))


class FieldNameFormatCleanForBigQuery(beam.DoFn):

  def process(self, element):
    """Replacing : in the field to _ for BigQuery loading."""
    element = json.loads(element)
    ret = {}
    for key, val in element.iteritems():
      ret[key.replace(':', '_')] = val
    yield json.dumps(ret)


if __name__ == '__main__':
  logging.getLogger().setLevel(logging.INFO)
  parser = argparse.ArgumentParser()
  # Input/Output parameters
  parser.add_argument('--project', dest='project', help='The cloud project.')
  parser.add_argument('--input', dest='input', help='Input storage.')
  parser.add_argument('--output', dest='output', help='Output storage.')
  parser.add_argument(
      '--testmode',
      dest='testmode',
      action='store_true',
      help='Runs the dataflow pipeline using DirectRunner.')

  known_args, pipeline_args = parser.parse_known_args()
  run(known_args, pipeline_args)
