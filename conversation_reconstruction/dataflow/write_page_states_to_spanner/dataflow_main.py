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

A dataflow pipeline to write data into Spanner

Run with:

  python dataflow_main.py
         --input_storage=YourInputDataInCloudStorage**
         --bigquery_table=YourBigQueryTable**
         --spanner_instance=SpannerInstanceID
         --spanner_database=SpannerDatabaseID --spanner_table=SpannerTableID
         --jobname=YourJobName
         --spanner_table_columns_config=JsonConfigFile
         --insert_deleted_comments****
         --testmode***
         --setup_file=./setup.py

Note:
  **Storage options: There are two ways to provide storage options: via input_storage or bigquery_table
  ***--testmode: optional on-off button that enables testmode of the dataflow pipeline,
              running on DirectRunner instead of DataflowRunner when turned on.
  ****--A special spanner writing tool for a specific purpose, writing deleted comments genereated from
      conversation reconstruction process.
"""
# -*- coding: utf-8 -*-


from __future__ import absolute_import
import argparse
import logging
import json
import datetime

import apache_beam as beam
from apache_beam.metrics.metric import Metrics
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import SetupOptions
from write_utils.write import SpannerWriter


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
    '--job_name=write-data-to-spanner-{jobname}'.format(jobname=known_args.jobname),
    '--max_num_workers=100'
  ])
  pipeline_options = PipelineOptions(pipeline_args)
  pipeline_options.view_as(SetupOptions).save_main_session = True
  logging.info("PIPELINE STARTED")
  print(pipeline_args)

  with beam.Pipeline(options=pipeline_options) as p:
    if known_args.input_storage is not None:
      # Read from cloud storage.
      input_data = (p | beam.io.ReadFromText(known_args.input_storage))
    else:
      # Read from BigQuery, the table has to already exist.
      input_data = (p | beam.io.Read(beam.io.BigQuerySource(
          query="SELECT * FROM %s" % known_args.bigquery_table, use_standard_sql=True)))
   # Main pipeline.
    p = (input_data | beam.ParDo(WriteToSpanner(known_args.spanner_instance, known_args.spanner_database,
                                                known_args.spanner_table, known_args.spanner_table_columns),
                                                known_args.insert_deleted_comments, known_args.input_storage))

class WriteToSpanner(beam.DoFn):
  def __init__(self, instance_id, database_id, table_id, table_columns):
    self.inserted_record = Metrics.counter(self.__class__, 'inserted_record')
    self.already_exists = Metrics.counter(self.__class__, 'already_exists')
    self.large_record = Metrics.counter(self.__class__, 'large_record')
    self.instance_id = instance_id
    self.database_id = database_id
    self.table_id = table_id
    self.table_columns = table_columns


  def start_bundle(self):
    self.table_columns = self.table_columns
    self.writer = SpannerWriter(self.instance_id, self.database_id)
    self.writer.create_table(self.table_id, self.table_columns)


  def process(self, element,insert_deleted_comments, input_storage):
    if input_storage is not None:
      # Data from cloud storage may be json incoded.
      element = json.loads(element)
    if insert_deleted_comments:
      # Add an artificial timestamp to the previously deleted comments to
      # preserve ordering
      delta = datetime.timedelta(seconds=1)
      timestamp = datetime.date(2001, 1, 1)
      for record in element['deleted_comments']:
        data = {'page_id': element['page_id'],
                'content': record[0],
                'parent_id': record[1],
                'indentation': record[2],
                'timestamp': datetime.date.strftime(timestamp, "%Y-%m-%dT%H:%M:%SZ")}
        timestamp = timestamp + delta
        try:
           self.writer.insert_data(self.table_id, data)
           self.inserted_record.inc()
        except Exception as e:
          if 'StatusCode.ALREADY_EXISTS' in str(e):
             self.already_exists.inc()
             pass
          else:
            raise Exception(e)
    else:
      try:
         self.writer.insert_data(self.table_id, element)
         self.inserted_record.inc()
      except Exception as e:
        if 'StatusCode.ALREADY_EXISTS' in str(e):
           self.already_exists.inc()
           pass
        else:
          raise Exception(e)



if __name__ == '__main__':
  logging.getLogger().setLevel(logging.INFO)
  parser = argparse.ArgumentParser()
  # input/output parameters.
  parser.add_argument('--input_storage',
                      dest='input_storage',
                      default=None,
                      help='Input storage of the data records to be written into Spanner.')
  parser.add_argument('--bigquery_table',
                      dest='bigquery_table',
                      default=None,
                      help='Input BigQuery table.')
  parser.add_argument('--spanner_instance',
                      dest='spanner_instance',
                      help='The id of the Spanner instance.')
  parser.add_argument('--spanner_database',
                      dest='spanner_database',
                      help='The id of the Spanner database.')
  parser.add_argument('--spanner_table',
                      dest='spanner_table',
                      help='The id of the Spanner table.')
  parser.add_argument('--spanner_table_columns_config',
                      dest='config_file',
                      default=None,
                      help='The config file in json format to specify columns.')
  parser.add_argument('--testmode',
                      dest='testmode',
                      action='store_true',
                      default=None,
                      help='(Optional) Run the pipeline in testmode.')
  parser.add_argument('--insert_deleted_comments',
                      dest='insert_deleted_comments',
                      action='store_true',
                      default=False,
                      help='(Optional) Run the pipeline for deleted comments.')
  parser.add_argument('--jobname',
                      dest='jobname',
                      default='',
                      help='The name of the dataflow job.')
  known_args, pipeline_args = parser.parse_known_args()
  if known_args.input_storage is None and known_args.bigquery_table is None:
    raise Exception("Please provide input storage/BigQuery table to run the pipeline.")
  if known_args.input_storage is not None and known_args.bigquery_table is not None:
    raise Exception("Input storage and BigQuery table cannot be both specifiedi.")
  if known_args.config_file is not None:
    with open(known_args.config_file, "r") as f:
      known_args.spanner_table_columns = json.load(f)
  run(known_args, pipeline_args)

