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

A dataflow pipeline to clean MediaWiki formats in comments and convert nested
array type to acceptable type in BigQuery.

Run with:

   python dataflow_content_clean.py --setup_file ./setup.py
   --input=InputStorage\
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
from wikiconv.conversation_reconstruction.construct_utils.utils.third_party.clean import content_clean

import apache_beam as beam
from apache_beam.metrics.metric import Metrics
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import SetupOptions

TIMEOUT = 2


def run(known_args, pipeline_args):
  """Main entry point; defines and runs the sharding pipeline."""

  if known_args.testmode:
    pipeline_args.append('--runner=DirectRunner')
  else:
    pipeline_args.append('--runner=DataflowRunner')

  pipeline_args.extend([
      '--project={project}'.format(project=known_args.project),
      '--staging_location=gs://{bucket}/staging'.format(
          bucket=known_args.bucket),
      '--temp_location=gs://{bucket}/tmp'.format(bucket=known_args.bucket),
      '--job_name=resultformatting-{}'.format(known_args.jobname),
      '--num_workers=80'
  ])
  pipeline_options = PipelineOptions(pipeline_args)
  pipeline_options.view_as(SetupOptions).save_main_session = True

  # Queries extracting the data
  with beam.Pipeline(options=pipeline_options) as p:
    results, error_log = (
        p | beam.io.ReadFromText(known_args.input)
        | beam.ParDo(FormatClean()).with_outputs('error_log', main='results'))
    results | 'WriteResult' >> beam.io.WriteToText(known_args.output)
    error_log | 'WriteErrorLog' >> beam.io.WriteToText(known_args.error_log)


class FormatClean(beam.DoFn):

  def __init__(self):
    self.processed_records = Metrics.counter(self.__class__,
                                             'processed_records')
    self.parsing_errors = Metrics.counter(self.__class__, 'parsing_errors')
    self.schema = 'ancestor_id,authors,cleaned_content,content,conversation_id,id,indentation,page_id,page_title,parent_id,replyTo_id,rev_id,timestamp,type,user_id,user_text'
    self.fields = self.schema.split(',')

  def clean_schema(self, x):
    res = {}
    for f in self.fields:
      if f in x:
        res[f] = x[f]
      else:
        res[f] = None
    return res

  def process(self, element):
    """Convert nested array field to array; clean the wikipedia webpage format."""
    element = json.loads(element)
    # Dry run of format cleanning in case of unexpected error.
    p = multiprocessing.Process(
        target=content_clean, name='subprocess', args=((element['content']),))
    p.start()
    p.join(TIMEOUT)
    if p.is_alive():
      self.parsing_errors.inc()
      p.terminate()
      p.join()
      yield beam.pvalue.TaggedOutput('error_log', json.dumps(element))
      element['cleaned_content'] = element['content']
    else:
      self.processed_records.inc()
      # MediaWiki formats cleaned only in the case of a success run of subprocess.
      element['cleaned_content'] = content_clean(element['content'])
    # Avoid nested arrays.
    temp = [
        u'{userid}:{username}'.format(
            userid=author[0] if author[0] is not None else 'ANONYMOUS',
            username=author[1] if author[1] is not None else 'ANONYMOUS')
        for author in element['authors']
    ]
    element['authors'] = temp
    yield json.dumps(self.clean_schema(element))


if __name__ == '__main__':
  logging.getLogger().setLevel(logging.INFO)
  parser = argparse.ArgumentParser()
  # Input/Output parameters
  parser.add_argument('--project', dest='project', help='The cloud project.')
  parser.add_argument('--bucket', dest='bucket', help='The cloud bucket.')
  parser.add_argument('--input', dest='input', help='Input storage.')
  parser.add_argument('--output', dest='output', help='Output storage.')
  parser.add_argument(
      '--error_log',
      dest='error_log',
      help='Cloud storage location to write error log.')
  parser.add_argument('--jobname', dest='jobname', help='The dataflow jobname.')
  parser.add_argument(
      '--testmode',
      dest='testmode',
      action='store_true',
      help='Runs the dataflow pipeline using DirectRunner.')

  known_args, pipeline_args = parser.parse_known_args()
  run(known_args, pipeline_args)
