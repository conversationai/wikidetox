
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
from construct_utils.conversation_constructor import Conversation_Constructor


LOG_INTERVAL = 1000

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
  renaming = "latest.rev_id_in_int as rev_id_in_int, latest.week as week, latest.year as year, latest.sha1 as sha1, latest.user_id as user_id, latest.format as format, latest.user_text as user_text, latest.timestamp as timestamp, latest.text as text, latest.page_title as page_title, latest.model as model, latest.page_namespace as page_namespace, latest.page_id as page_id, latest.rev_id as rev_id, latest.comment as comment, latest.user_ip as user_ip, latest.truncated as truncated, latest.records_count as records_count, latest.record_index as record_index"
  get_max_query= "SELECT * FROM (SELECT * FROM %s, (SELECT %s FROM (SELECT %s FROM %s as latest INNER JOIN (SELECT max(rev_id_in_int) as max_rev_id FROM %s WHERE week < %d or year < %d GROUP BY week, year, page_id) as previous_max"%(known_args.input_table, renaming, renaming, known_args.input_table, known_args.input_table, known_args.week, known_args.year)
  get_latest_query = " ON previous_max.max_rev_id == latest.rev_id_in_int) as latest LEFT JOIN (SELECT page_id FROM %s WHERE week == %d and year == %d) as cur ON latest.page_id == cur.page_id)) as ingested"%(known_args.input_table, known_args.week, known_args.year) 
  join_query = " LEFT JOIN (SELECT ps_tmp.* FROM %s as ps_tmp INNER JOIN (SELECT MAX(rev_id) as max_rid, page_id FROM %s GROUP BY page_id) as tmp ON tmp.page_id == ps_tmp.page_id and ps_tmp.rev_id == tmp.max_rid) as page_state ON ingested.page_id == page_state.ps_tmp.page_id"%(known_args.input_page_state_table,known_args.input_page_state_table)
  condition_query = " WHERE week==%d and year==%d ORDER BY rev_id_in_int"%(known_args.week, known_args.year)
  read_query = get_max_query + get_latest_query + join_query + condition_query
  with beam.Pipeline(options=pipeline_options) as p:

    # Read the text file[pattern] into a PCollection.
    reconstruction_results, page_states = (p | beam.io.Read(beam.io.BigQuerySource(query=read_query, validate=True)) 
                   | beam.Map(lambda x: (x['ingested_page_id'], x))
                   | beam.GroupByKey()
                   | beam.ParDo(ReconstructConversation()).with_outputs('page_states', main = 'reconstruction_results'))
    page_states | "WritePageStates" >> beam.io.Write(bigquery_io.BigQuerySink(known_args.page_states_output_table, schema=known_args.page_states_output_schema, write_disposition='WRITE_APPEND', validate=True))
    reconstruction_results | "WriteReconstructedResults" >> beam.io.Write(bigquery_io.BigQuerySink(known_args.output_table, schema=known_args.output_schema, validate=True))


class ReconstructConversation(beam.DoFn):
  def QueryResult2json(self, query_res):
      ret = {} 
      for key, val in query_res.items():
          if 'ingested_' in key:
             ret[key[9:]] = val
          elif 'page_state_ps_tmp_' in key:
             ret[key[18:]] = val
          else:
             ret[key] = val
      return ret

  def process(self, pairs):
    rows = pairs[1] 
    page_id = pairs[0]
    logging.info('USERLOG: Reconstruction work start on page: %s'%page_id)
    revision = {}
    processor = Conversation_Constructor()
    last_revision = 'None'
    error_encountered = False
    cnt = 0
    last_page_state = None
    first_time = True
    for cur_revision in rows:
        cur_revision = self.QueryResult2json(cur_revision)
          
        if cur_revision['record_index'] == 0: 
           revision = cur_revision
        else:
           revision['text'] += cur_revision['text']
        if cur_revision['record_index'] == cur_revision['records_count'] - 1:
           if first_time:
              first_time = False
              if cur_revision['page_state']:
                 logging.info('Page %s existed: loading page state, last revision: %s'%(cur_revision['page_id'], cur_revision['rev_id'])) 
                 processor.load(cur_revision['page_state'], cur_revision['deleted_comments'], cur_revision['conversation_id'], cur_revision['authors'], cur_revision['text'])
                 continue
           cnt += 1
           page_state, actions = processor.process(revision, DEBUGGING_MODE = False)
           last_revision = cur_revision['rev_id']
           last_page_state = page_state 
           for action in actions:
               yield action
           if cnt % LOG_INTERVAL == 0:
              yield beam.pvalue.TaggedOutput('page_states', page_state)
    if last_page_state:
       yield beam.pvalue.TaggedOutput('page_states', last_page_state)
    if not(error_encountered):
       logging.info('USERLOG: Reconstruction on page %s complete! last revision: %s' %(page_id, last_revision))


if __name__ == '__main__':
  logging.getLogger().setLevel(logging.INFO)
  parser = argparse.ArgumentParser()
  # Input BigQuery Table
  parser.add_argument('--input_table',
                      dest='input_table',
                      default='wikidetox_conversations.ingested_all',
                      help='Input table with ingested revisions.')
  parser.add_argument('--input_page_state_table',
                      dest='input_page_state_table',
                      default='wikidetox_conversations.page_states',
                      help='Input page states table from previous reconstruction process.')

  parser.add_argument('--week',
                      dest='week',
                      default=5,
                      help='The week of data you want to process')
  parser.add_argument('--year',
                      dest='year',
                      default=2001,
                      help='The year that the week is in')
  # Ouput BigQuery Table
  page_states_output_schema = 'rev_id:INTEGER, page_id:STRING, page_state:STRING, deleted_comments:STRING, conversation_id:STRING, authors:STRING'  
  parser.add_argument('--page_states_output_table',
                      dest='page_states_output_table',
                      default='wikidetox-viz:wikidetox_conversations.page_states',
                      help='Output page state table for reconstruction.')
  parser.add_argument('--page_states_output_schema',
                      dest='page_states_output_schema',
                      default=page_states_output_schema,
                      help='Page states output table schema.')

  output_schema = 'user_id:STRING,user_text:STRING, timestamp:STRING, content:STRING, parent_id:STRING, replyTo_id:STRING, indentation:INTEGER,page_id:STRING,page_title:STRING,type:STRING, id:STRING,rev_id:STRING,conversation_id:STRING, authors:STRING'  
  parser.add_argument('--output_table',
                      dest='output_table',
                      default='wikidetox-viz:wikidetox_conversations.reconstructed',
                      help='Output result table for reconstruction.')
  parser.add_argument('--output_schema',
                      dest='output_schema',
                      default=output_schema,
                      help='Output table schema.')
  known_args, pipeline_args = parser.parse_known_args()
  known_args.week = int(known_args.week)
  known_args.year = int(known_args.year)


  known_args.output_table = 'wikidetox-viz:wikidetox_conversations.reconstructed_at_week%d_year%d'%(known_args.week, known_args.year)

  run(known_args, pipeline_args)

