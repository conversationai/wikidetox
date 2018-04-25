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

Dataflow Main

A dataflow pipeline to ingest the Wikipedia dump from 7zipped xml files to json.

Run with:

python dataflow_main.py --setup_file ./setup.py 

"""

from __future__ import absolute_import

import argparse
import logging
import subprocess
from threading import Timer
import json
import sys
import zlib
import copy
from os import path
import xml.sax
from ingest_utils import wikipedia_revisions_ingester as wiki_ingester
import math
import os
import time

import apache_beam as beam
from apache_beam.metrics.metric import Metrics
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import SetupOptions
from apache_beam.io import ReadFromText
from apache_beam.io import WriteToText
from apache_beam.io import filesystems
from apache_beam.pipeline import AppliedPTransform
from apache_beam.io.gcp import bigquery #WriteToBigQuery
from datetime import datetime

LOGGING_THERESHOLD = 500

def run(known_args, pipeline_args):
  """Main entry point; defines and runs the ingestion pipeline."""

  pipeline_args.extend([
    '--runner=DataflowRunner',
    '--project=wikidetox-viz',
    '--staging_location=gs://wikidetox-viz-dataflow/staging',
    '--temp_location=gs://wikidetox-viz-dataflow/tmp',
    '--job_name=ingest-job-on-previously-stuck-revisions',
    '--num_workers=30',
  ])

  pipeline_options = PipelineOptions(pipeline_args)
  pipeline_options.view_as(SetupOptions).save_main_session = True
  with beam.Pipeline(options=pipeline_options) as p:
    pcoll = (p | ReadFromText(known_args.input)
                   | beam.ParDo(WriteDecompressedFile())
                   | beam.Map(lambda x: ('{week}at{year}'.format(week=x['week'], year=x['year']), x))
                   | beam.GroupByKey()
                   | beam.ParDo(WriteToStorage()))

class WriteToStorage(beam.DoFn):
  def process(self, element):
      (key, val) = element
      week, year = [int(x) for x in key.split('at')]
      path = known_args.output + 'date-{week}at{year}/revisions.json'.format(week=week, year=year)
      logging.info('USERLOG: Write to path %s.'%path)
      outputfile = filesystems.FileSystems.create(path)
      for output in val:
          outputfile.write(json.dumps(output) + '\n')
      outputfile.close() 


def add_week_year_fields(s):
    dic = json.loads(s) 
    dt = datetime.strptime(dic['timestamp'], "%Y-%m-%dT%H:%M:%SZ")
    year, week = dt.isocalendar()[:2]
    dic['year'] = year
    dic['week'] = week
    return dic

def is_in_range(pid):
    for lr, ur in ingest_range:
        if pid >= lr and pid <= ur:
           return True
    return False

def is_in_time_range(ts):
    dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")
    if not(dt.year == 2017): return (dt.year < 2017) 
    else:
       return (dt.month < 6)

class WriteDecompressedFile(beam.DoFn):
  def __init__(self):
      self.processed_revisions = Metrics.counter(self.__class__, 'processed_revisions')

  def process(self, element):
    chunk_name = element

    in_file_path = path.join('gs://wikidetox-viz-dataflow/raw-downloads-20180201/20180201-dumps/', chunk_name)

    logging.info('USERLOG: Running gsutil %s ./' % in_file_path)
    cp_local_cmd = (['gsutil', 'cp', in_file_path, './'])
    subprocess.call(cp_local_cmd)

    logging.info('USERLOG: Running ingestion process on %s' % chunk_name)
    ingestion_cmd = ['python2', '-m', 'ingest_utils.run_ingester', '-i', chunk_name]
    ingest_proc = subprocess.Popen(ingestion_cmd, stdout=subprocess.PIPE, bufsize = 4096)
    cnt = 0
    maxsize = 0
    last_revision = 'None'
    last_completed = time.time()
    for i, line in enumerate(ingest_proc.stdout):
      try:
          content = json.loads(line) 
      except:
         revid = line 
         logging.info('CHUNK {chunk}: revision {revid} ingested, time elapsed: {time}.'.format(chunk=chunk_name, revid=revid, time=time.time() - last_completed))
         last_completed = time.time()
         continue
      self.processed_revisions.inc()
      ret = add_week_year_fields(line)
      if is_in_range(int(content['page_id'])) and is_in_time_range(content['timestamp']):
         last_revision = content['rev_id']
         cnt += 1
         yield ret
      logging.info('CHUNK {chunk}: revision {revid} ingested, time elapsed: {time}.'.format(chunk=chunk_name, revid=last_revision, time=time.time() - last_completed))
      last_completed = time.time()
      maxsize = max(maxsize, sys.getsizeof(line))
    logging.info('USERLOG: Ingestion on file %s complete! %s lines emitted, maxsize: %d, last_revision %s' % (chunk_name, cnt, maxsize, last_revision))

if __name__ == '__main__':
  logging.getLogger().setLevel(logging.INFO)
  parser = argparse.ArgumentParser()
  parser.add_argument('--input',
                      dest='input',
                      default='gs://wikidetox-viz-dataflow/input_lists/7z_file_list_reingest',
                      help='Input file to process.')
  # Destination Cloud storage Folder 
  parser.add_argument('--output',
                      dest='output',
                      default='gs://wikidetox-viz-dataflow/reingested/',
                      help='Output storage.')

  known_args, pipeline_args = parser.parse_known_args()
  ingest_range = [[5137452, 5149115], [13135007,13252449],[51894080,52312206],[42663462,42930511],[952461, 972044],[2515120,2535917],[4684994,4750440]]
  run(known_args, pipeline_args)
