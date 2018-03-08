
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

python dataflow_main.py --setup_file ./setup.py
"""
from __future__ import absolute_import
import argparse
import logging
import subprocess
import json
from os import path
import urllib2
import traceback
from google.cloud import bigquery as bigquery_op 
from avro import schema, datafile, io
import copy
import sys

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import SetupOptions
from apache_beam.io.avroio import ReadFromAvro 
from apache_beam.io import filesystems


LOG_INTERVAL = 100

SCHEMA_STR = """{
    "type": "record",
    "name": "ingested-sharded",
    "namespace": "AVRO",
    "fields": [
        {   "name": "sha1",           "type": ["string" ,"null"]   },
        {   "name": "user_id",        "type": ["string" ,"null"]   },
        {   "name": "format",         "type": ["string" ,"null"]   },
        {   "name": "user_text",      "type": ["string" ,"null"]   },
        {   "name": "timestamp",      "type": ["string" ,"null"]   },
        {   "name": "text",           "type": ["string" ,"null"]   },
        {   "name": "page_title",     "type": ["string" ,"null"]   },
        {   "name": "model",          "type": ["string" ,"null"]   },
        {   "name": "page_namespace", "type": ["string" ,"null"]   },
        {   "name": "page_id",        "type": ["string" ,"null"]   },
        {   "name": "rev_id",         "type": ["string" ,"null"]   },
        {   "name": "comment",        "type": ["string" ,"null"]   },
        {   "name": "user_ip",        "type": ["string" ,"null"]   },
        {   "name": "truncated",      "type": ["boolean","null"]   },
        {   "name": "records_count",  "type": ["int"    ,"null"]   },
        {   "name": "record_index",   "type": ["int"    ,"null"]   },
        {   "name": "week",           "type": ["int"    ,"null"]   },
        {   "name": "year",           "type": ["int"    ,"null"]   },
        {   "name": "rev_id_in_int",  "type": ["int"    ,"null"]   }
    ]
}"""
 
SCHEMA = schema.parse(SCHEMA_STR)

def run(known_args, pipeline_args):
  """Main entry point; defines and runs the reconstruction pipeline."""

  pipeline_args.extend([
    '--runner=DataflowRunner',
    '--project=wikidetox-viz',
    '--staging_location=gs://wikidetox-viz-dataflow/staging',
    '--temp_location=gs://wikidetox-viz-dataflow/tmp',
    '--job_name=shard-{table}'.format(table=known_args.category),
    '--num_workers=30'])
  pipeline_options = PipelineOptions(pipeline_args)
  pipeline_options.view_as(SetupOptions).save_main_session = True
  jobname = 'shard-{table}'.format(table=known_args.category)

  # Queries extracting the data
  groupby_mapping = lambda x: (x['page_id'], x)
  with beam.Pipeline(options=pipeline_options) as p:
       pcoll = (p | ReadFromAvro(known_args.input) 
                 | beam.Map(lambda x: ('{year}'.format(year=x['year']), x))
                 | beam.GroupByKey()
                 | beam.ParDo(WriteToStorage()))

class WriteToStorage(beam.DoFn):
  def start_bundle(self):
    self.rec_writer = io.DatumWriter(SCHEMA)
    self.outputfile = None
  def process(self, element):
      (key, val) = element
      #week, year = [int(x) for x in key.split('at')]
      year = int(key)
      if self.outputfile == None:
         cnt = 0
#         path = known_args.output + 'date-{week}at{year}/revisions-{index}.avro'.format(week=week, year=year, index=cnt)
         path = known_args.output + 'date-{year}/revisions-{index}.avro'.format(year=year, index=cnt)
         while filesystems.FileSystems.exists(path):
             cnt += 1
#             path = known_args.output + 'date-{week}at{year}/revisions-{index}.avro'.format(week=week, year=year, index=cnt)
             path = known_args.output + 'date-{year}/revisions-{index}.avro'.format(week=week, year=year, index=cnt)
         logging.info('USERLOG: Write to path %s.'%path)
         self.outputfile = filesystems.FileSystems.create(path)
         self.df_writer = datafile.DataFileWriter(self.outputfile, self.rec_writer, writers_schema = SCHEMA)
      for output in val:
          self.df_writer.append(output)
  def finish_bundle(self):
      if not(self.outputfile == None):
         self.df_writer.close()
         self.outputfile.close()



if __name__ == '__main__':
  logging.getLogger().setLevel(logging.INFO)
  parser = argparse.ArgumentParser()

  # Input/Output parameters
  parser.add_argument('--category',
                      dest='category',
                      help='Specify the job category: long (pages), short (pages),test.')
  parser.add_argument('--input',
                      dest='input',
                      help='Input storage.')
  parser.add_argument('--output',
                      dest='output',
                      help='Output storage.')

  known_args, pipeline_args = parser.parse_known_args()
  run(known_args, pipeline_args)
