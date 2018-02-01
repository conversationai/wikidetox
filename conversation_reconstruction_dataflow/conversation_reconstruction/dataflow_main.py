
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

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import SetupOptions
from apache_beam.io.gcp import bigquery as bigquery_io 

LOG_INTERVAL = 5

def run(known_args, pipeline_args):
  """Main entry point; defines and runs the reconstruction pipeline."""

  pipeline_args.extend([
    '--runner=DataflowRunner',
    '--project=wikidetox-viz',
    '--staging_location=gs://wikidetox-viz-dataflow/staging',
    '--temp_location=gs://wikidetox-viz-dataflow/tmp',
    '--job_name=reconstruction-test',
    '--num_workers=5',
    '--extra_package=third_party/mwparserfromhell.tar.gz'
  ])


  pipeline_options = PipelineOptions(pipeline_args)
  pipeline_options.view_as(SetupOptions).save_main_session = True
  with beam.Pipeline(options=pipeline_options) as p:

    # Read the text file[pattern] into a PCollection.
    filenames = (p | beam.io.Read(beam.io.BigQuerySource(query='SELECT page_id as page_id FROM [wikidetox-viz:wikidetox_conversations.page_id_list] WHERE page_id < \"%s\" and page_id >= \"%s\" '%(known_args.page_id_upper_bound, known_args.page_id_lower_bound), validate=True)) 
                   | beam.ParDo(ReconstructConversation())
                   | beam.io.Write(bigquery_io.BigQuerySink(known_args.output_table, schema=known_args.output_schema, validate=True)))

class ReconstructConversation(beam.DoFn):
  def process(self, row):

    input_table = 'wikidetox_conversations.ingested' 
    page_id = row['page_id']
    logging.info('USERLOG: Work start on page: %s'%page_id)

    client = bigquery_op.Client(project='wikidetox-viz')
    query_content = "SELECT week, year FROM (SELECT WEEK(timestamp) as week, YEAR(timestamp) as year FROM %s WHERE page_id = \"%s\" ORDER BY timestamp) GROUP BY week, year"%(input_table, page_id)
    query = query_content 
    query_job = client.run_sync_query(query)
    query_job.run()
    rev_ids = []
    weeks = []

    for row in query_job.rows:
        weeks.append({'week': row[0], 'year': row[1]})
    logging.info('Processing %d weeks of revisions from page %s'%(len(weeks), page_id))

    construction_cmd = ['python2', '-m', 'construct_utils.run_constructor', '--table', input_table, '--weeks', json.dumps(weeks)]
    construct_proc = subprocess.Popen(construction_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize = 4096)
    last_revision = 'None'
   
    cnt = 0 

    error_encountered = False
    error_log = ""
    for i, line in enumerate(construct_proc.stdout): 
        try:
           output = json.loads(line)
        except:
           error_log += line + '\n'
           error_encountered = True
           continue
        last_revision = output['rev_id']
        if cnt % LOG_INTERVAL == 0:
           logging.info('DEBUGGING INFO: %d revision(reivision id %s) on page %s output: %s'%(cnt, last_revision, page_id, line))
        yield output
        cnt += 1
    if error_encountered:
       logging.info('USERLOG: Error while running the reconstruction process on page %s' % (page_id))
       logging.info('USERLOG: reconstruction process on page %s stopped at revision %s' % (page_id, last_revision))
       logging.info('ERROR ENCOUNTERED: %s' %(error_log))
       for i, line in enumerate(construct_proc.stderr):
           logging.info('ERRORLOG: %s' % (line))
 
    if not(error_encountered):
       logging.info('USERLOG: Reconstruction on page %s complete! last revision: %s' %(page_id, last_revision))


if __name__ == '__main__':
  logging.getLogger().setLevel(logging.INFO)
  parser = argparse.ArgumentParser()
  # Input BigQuery Table
  parser.add_argument('--upper',
                      dest='page_id_upper_bound',
                      default='40932797',
                      help='upper bound of the page id you want to process')
  parser.add_argument('--lower',
                      dest='page_id_lower_bound',
                      default='40932796',
                      help='lower bound of the page id you want to process')
  # Ouput BigQuery Table
  output_schema = 'sha1:STRING,user_id:STRING,format:STRING,user_text:STRING,timestamp:STRING,text:STRING,page_title:STRING,model:STRING,page_namespace:STRING,page_id:STRING,rev_id:STRING,comment:STRING, user_ip:STRING, truncated:BOOLEAN,records_count:INTEGER,record_index:INTEGER'
  parser.add_argument('--output_table',
                      dest='output_table',
                      default='wikidetox-viz:wikidetox_conversations.reconstructed',
                      help='Output table for reconstruction.')
  output_schema = 'user_id:STRING,user_text:STRING, timestamp:STRING, content:STRING, parent_id:STRING, replyTo_id:STRING, indentation:INTEGER,page_id:STRING,page_title:STRING,type:STRING, id:STRING,rev_id:STRING,conversation_id:STRING, authors:STRING'  
  parser.add_argument('--output_schema',
                      dest='output_schema',
                      default=output_schema,
                      help='Output table schema.')
  known_args, pipeline_args = parser.parse_known_args()
  known_args.output_table = 'wikidetox-viz:wikidetox_conversations.reconstructed_%sto%s'%(known_args.page_id_lower_bound, known_args.page_id_upper_bound)

  run(known_args, pipeline_args)




