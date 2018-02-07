
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
    '--num_workers=30',
    '--extra_package=third_party/mwparserfromhell.tar.gz'
  ])
  pipeline_options = PipelineOptions(pipeline_args)
  pipeline_options.view_as(SetupOptions).save_main_session = True
  renaming = "latest.rev_id_in_int as rev_id_in_int, latest.week as week, latest.year as year, latest.sha1 as sha1, latest.user_id as user_id, latest.format as format, latest.user_text as user_text, latest.timestamp as timestamp, latest.text as text, latest.page_title as page_title, latest.model as model, latest.page_namespace as page_namespace, latest.page_id as page_id, latest.rev_id as rev_id, latest.comment as comment, latest.user_ip as user_ip, latest.truncated as truncated, latest.records_count as records_count, latest.record_index as record_index"
  within_time_range = '((week >= {lw} and year == {ly}) or year > {ly}) and ((week <= {uw} and year == {uy}) or year < {uy})'.format(lw = known_args.lower_week, ly = known_args.lower_year, uw = known_args.upper_week, uy = known_args.upper_year)
  ingested_data_within_time = "(SELECT * FROM {input_table} WHERE {time_range}), ".format(input_table=known_args.input_table, time_range=within_time_range)
  rev_id_of_latest_processed = "(select rev_id_in_int from (select rev_id_in_int, row_number() over (partition by page_id order by timestamp desc, rev_id_in_int desc) as seqnum from {input_table} WHERE (week < {lw} and year == {ly}) or year < {ly}) where seqnum < 2) as previous_max ".format(input_table=known_args.input_table, lw=known_args.lower_week, ly=known_args.lower_year)
  on_selected_pages= "INNER JOIN (SELECT page_id FROM {input_table} WHERE week == {w} and year == {y} GROUP BY page_id) as cur ON latest.page_id == cur.page_id) ".format(input_table=known_args.input_table, w=known_args.week, y=known_args.year)
  get_latest_revision = "(SELECT {renamed} FROM (SELECT {renamed} FROM {input_table} as latest INNER JOIN ".format(renamed=renaming, input_table=known_args.input_table) + rev_id_of_latest_processed + "ON previous_max.rev_id_in_int == latest.rev_id_in_int) as latest " + on_selected_pages
  ingested_all = "(SELECT * FROM " + ingested_data_within_time + get_latest_revision + ") as ingested "
  previous_page_states = "(SELECT ps_tmp.* FROM {page_states} as ps_tmp INNER JOIN (SELECT MAX(timestamp) as max_timestamp, page_id FROM {page_states} GROUP BY page_id) as tmp ON tmp.page_id == ps_tmp.page_id and ps_tmp.timestamp== tmp.max_timestamp) as page_state ".format(page_states=known_args.input_page_state_table)
  read_query = "SELECT * FROM " + ingested_all + "LEFT JOIN " + previous_page_states + "ON ingested.page_id == page_state.ps_tmp.page_id ORDER BY ingested.timestamp, ingested.rev_id_in_int"
  if known_args.initial_reconstruction:
     read_query = "SELECT * FROM {input_table} WHERE {time_range} ORDER BY timestamp, rev_id_in_int".format(input_table=known_args.input_table, time_range=within_time_range) 
     groupby_mapping = lambda x: (x['page_id'], x)
  else:
     groupby_mapping = lambda x: (x['ingested_page_id'], x)
  with beam.Pipeline(options=pipeline_options) as p:
    reconstruction_results, page_states = \
                (p | beam.io.Read(beam.io.BigQuerySource(query=read_query, validate=True)) 
                   # Read from ingested table joined with previously reconstructed page states
                   | beam.Map(groupby_mapping) | beam.GroupByKey()
                   # Groupby by page_id
                   | beam.ParDo(ReconstructConversation()).with_outputs('page_states', main = 'reconstruction_results'))
                   # Reconstruct the conversations
    page_states | "WritePageStates" >> beam.io.Write(bigquery_io.BigQuerySink(known_args.page_states_output_table, schema=known_args.page_states_output_schema, write_disposition='WRITE_APPEND', validate=True))
    # Write the page states to BigQuery
    reconstruction_results | "WriteReconstructedResults" >> beam.io.Write(bigquery_io.BigQuerySink(known_args.output_table, schema=known_args.output_schema, validate=True))
    # Write the reconstructed results to BigQuery


class ReconstructConversation(beam.DoFn):
  def QueryResult2json(self, query_res):
      """
         Clear formatting introduced by join.
         Input: BigQuery result in a dictionary with prefixes added to fields resulted from join. 
         Output: Clear the prefixes to match with the field notations in the following code.
      """
      ret = {} 
      for key, val in query_res.items():
          if 'ingested_' in key:
             ret[key[9:]] = val
          elif ('page_state_ps_tmp_' in key) and not(key == 'page_state_ps_tmp_timestamp'):
             ret[key[18:]] = val
          elif not(key == 'page_state_ps_tmp_timestamp'):
             ret[key] = val
      return ret

  def process(self, pairs):
    rows = pairs[1] 
    page_id = pairs[0]
    if page_id == None: return
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
        if not('rev_id' in cur_revision):
           continue
        if cur_revision['record_index'] == 0: 
           revision = cur_revision
        else:
           revision['text'] += cur_revision['text']
        if cur_revision['record_index'] == cur_revision['records_count'] - 1:
           if first_time and not(known_args.initial_reconstruction):
              first_time = False
              if cur_revision['page_state']:
                 logging.info('Page %s existed: loading page state, last revision: %s'%(revision['page_id'], revision['rev_id'])) 
                 processor.load(revision['page_state'], revision['deleted_comments'], revision['conversation_id'], revision['authors'], revision['text'])
                 continue
           cnt += 1
           last_revision = revision['rev_id']
           try:
              page_state, actions = processor.process(revision, DEBUGGING_MODE = False)
           except: 
              logging.info('ERRORLOG: Reconstruction on page %s failed! last revision: %s' %(page_id, last_revision))
              raise ValueError
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
                      default=None,
                      help='The week of data you want to process')
  parser.add_argument('--year',
                      dest='year',
                      default=None,
                      help='The year that the week is in')
  parser.add_argument('--week_lowerbound',
                      dest='lower_week',
                      default=None,
                      help='The start week of data you want to process')
  parser.add_argument('--year_lowerbound',
                      dest='lower_year',
                      default=None,
                      help='The year of the start week.')
  parser.add_argument('--week_upperbound',
                      dest='upper_week',
                      default=None,
                      help='The end week of data you want to process')
  parser.add_argument('--year_upperbound',
                      dest='upper_year',
                      default=None,
                      help='The year of the end week.')
 
  # Ouput BigQuery Table

  page_states_output_schema = 'rev_id:INTEGER, page_id:STRING, page_state:STRING, deleted_comments:STRING, conversation_id:STRING, authors:STRING, timestamp:STRING'  
  parser.add_argument('--page_states_output_table',
                      dest='page_states_output_table',
                      default='wikidetox-viz:wikidetox_conversations.page_states',
                      help='Output page state table for reconstruction.')
  parser.add_argument('--page_states_output_schema',
                      dest='page_states_output_schema',
                      default=page_states_output_schema,
                      help='Page states output table schema.')

  output_schema = 'user_id:STRING, user_text:STRING, timestamp:STRING, content:STRING, parent_id:STRING, replyTo_id:STRING, indentation:INTEGER, page_id:STRING, page_title:STRING, type:STRING, id:STRING, rev_id:STRING, conversation_id:STRING, authors:STRING'  
  parser.add_argument('--output_schema',
                      dest='output_schema',
                      default=output_schema,
                      help='Output table schema.')
  parser.add_argument('--initial_reconstruction',
                      dest='initial_reconstruction',
                      default=False,
                      help='Is this the first time reconstruction, meaning no existing page states processed.')

  known_args, pipeline_args = parser.parse_known_args()
  if known_args.week:
     known_args.lower_week, known_args.upper_week = int(known_args.week), int(known_args.week)
     known_args.lower_year, known_args.upper_year = int(known_args.year), int(known_args.year)
  known_args.lower_week = int(known_args.lower_week)
  known_args.lower_year = int(known_args.lower_year) 
  known_args.upper_week = int(known_args.upper_week)
  known_args.upper_year = int(known_args.upper_year)
  known_args.output_table = 'wikidetox-viz:wikidetox_conversations.reconstructed_from_week%d_year%dto_week%d_year%d'%(known_args.lower_week, known_args.lower_year, known_args.upper_week, known_args.upper_year)
  run(known_args, pipeline_args)

