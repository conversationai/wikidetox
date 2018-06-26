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

  python dataflow_main.py --input_storage=YourInputDataInCloudStorage --spanner_instance=SpannerInstanceID
         --spanner_database=SpannerDatabaseID --spanner_table=SpannerTableID
         (Optional, if not provided, this will be inferred from cloud storage) --spanner_table_columns=ListOfColumnNames
         (Optional) --testmode
"""

from __future__ import absolute_import
import argparse
import logging
import json

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
    '--job_name=write-data-into-spanner',
    '--max_num_workers=20'
  ])
  pipeline_options = PipelineOptions(pipeline_args)
  pipeline_options.view_as(SetupOptions).save_main_session = True
  logging.info("PIPELINE STARTED")

  with beam.Pipeline(options=pipeline_options) as p:
    # Main Pipeline
    p = (p | beam.io.ReadFromText(known_args.input_storage)
         | beam.ParDo(WriteToSpanner(known_args.spanner_instance, known_args.spanner_database,
                                     known_args.spanner_table, known_args.spanner_table_columns)))

class WriteToSpanner(beam.DoFn):
  def __init__(self, instance_id, database_id, table_id, table_columns):
    self.inserted_record = Metrics.counter(self.__class__, 'inserted_record')
    self.already_exists = Metrics.counter(self.__class__, 'already_exists')
    self.instance_id = instance_id
    self.database_id = database_id
    self.table_id = table_id
    self.table_columns = table_columns


  def start_bundle():
    self.writer = SpannerWriter(self.instance_id, self.database_id)
    self.writer.create_table(self.table_id, self.table_columns)


  def process(self, element):
    element = json.loads(element)
    logging.info("RECORD PAGE %s INSERTED." % element['page_id'])
    if table_columns is None:
      table_columns = sorted(element.keys())
    else:
      table_columns = sorted(table_columns)
    table_columns = tuple(table_columns)
    try:
       self.writer.insert_data(table_id, [(element[key] for key in table_columns)])
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
                      help='Input storage of the data records to be written into Spanner.')
  parser.add_argument('--spanner_instance',
                      dest='spanner_instance',
                      help='The id of the Spanner instance.')
  parser.add_argument('--spanner_database',
                      dest='spanner_database',
                      help='The id of the Spanner database.')
  parser.add_argument('--spanner_table',
                      dest='spanner_table',
                      help='The id of the Spanner table.')
  parser.add_argument('--spanner_table_columns',
                      dest='spanner_table_columns',
                      type=list,
                      default=None,
                      help='(Optional) The columns in the spanner table.')
  parser.add_argument('--testmode',
                      dest='testmode',
                      action='store_true',
                      default=None,
                      help='(Optional) Run the pipeline in testmode.')

  known_args, pipeline_args = parser.parse_known_args()
  run(known_args, pipeline_args)

