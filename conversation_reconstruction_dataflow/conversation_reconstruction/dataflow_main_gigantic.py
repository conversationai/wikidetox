
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
import sys

import apache_beam as beam
import copy
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import SetupOptions
from apache_beam.io.gcp import bigquery as bigquery_io 
from construct_utils.conversation_constructor import Conversation_Constructor


LOG_INTERVAL = 100

def run(known_args, pipeline_args):
  """Main entry point; defines and runs the reconstruction pipeline."""

  pipeline_args.extend([
    '--runner=DirectRunner',
    '--project=wikidetox-viz',
    '--staging_location=gs://wikidetox-viz-dataflow/staging',
    '--temp_location=gs://wikidetox-viz-dataflow/tmp',
    '--job_name=reconstruction-super-long-page-{pageid}-week{lw}year{ly}-week{uw}year{uy}'.format(pageid=known_args.page_id, lw=known_args.lower_week, ly=known_args.lower_year, uw=known_args.upper_week, uy=known_args.upper_year),
    '--num_workers=5',
    '--extra_package=third_party/mwparserfromhell.tar.gz'
  ])
  jobname = 'reconstruction-super-long-page-{pageid}-week{lw}year{ly}-week{uw}year{uy}'.format(pageid=known_args.page_id, lw=known_args.lower_week, ly=known_args.lower_year, uw=known_args.upper_week, uy=known_args.upper_year)
  pipeline_options = PipelineOptions(pipeline_args)
  pipeline_options.view_as(SetupOptions).save_main_session = True

  debug_page = ''#'and page_id = \'%s\''%(known_args.page_id)
  debug1 = ''#'where page_id = \'%s\''%(known_args.page_id)

  within_time_range = '((week >= {lw} and year = {ly}) or year > {ly}) and ((week <= {uw} and year = {uy}) or year < {uy})'.format(lw = known_args.lower_week, ly = known_args.lower_year, uw = known_args.upper_week, uy = known_args.upper_year)
  before_time_range = '(week < {lw} and year = {ly}) or year < {ly}'.format(lw=known_args.lower_week, ly=known_args.lower_year) 
  before_time_range_1 = '(week(timestamp) < {lw} and year(timestamp) = {ly}) or year(timestamp)< {ly}'.format(lw=known_args.lower_week, ly=known_args.lower_year) 

  ingested_revs_for_processing = "SELECT * FROM {input_table} WHERE {time_range} {debug}".format(input_table=known_args.input_table, time_range=within_time_range, debug=debug_page)
  last_revision_processed = "SELECT * FROM {input_table} WHERE {before_time_range} {debug} ORDER BY timestamp DESC, rev_id_in_int DESC LIMIT 1".format(input_table=known_args.input_table, before_time_range=before_time_range, debug=debug_page)
  last_page_state = "SELECT * FROM {page_state_table} {debug} WHERE {before_time_range} ORDER BY timestamp DESC, rev_id DESC LIMIT 1".format(before_time_range=before_time_range_1, page_state_table=known_args.input_page_state_table, debug=debug1)
  with beam.Pipeline(options=pipeline_options) as p:
    if known_args.read_input_from_cloud:
       to_be_processed = (p | 'Read_to_be_processed' >> beam.io.ReadFromText("gs://wikidetox-viz-dataflow/testing/%s.input_revs*"%jobname))
       # Read from ingested table to get revisions to process
       last_revision = (p | 'Retrieve_last_revision' >> beam.io.ReadFromText("gs://wikidetox-viz-dataflow/testing/%s.last_rev*"%jobname))
       # Read from ingested table to get last processed revision 
       page_state = (p | 'Retrieve_page_state' >> beam.io.ReadFromText("gs://wikidetox-viz-dataflow/testing/%s.page_states*"%jobname))
       # Read from page state table to get the page states recorded from previous processing steps
       mapping = lambda x: (json.loads(x)['page_id'], json.loads(x))
    else:
       to_be_processed = (p | 'Read_to_be_processed' >> beam.io.Read(beam.io.BigQuerySource(query=ingested_revs_for_processing, validate=True, use_standard_sql=True)))
       # Read from ingested table to get revisions to process
       last_revision = (p 
            | 'Retrieve_last_revision' >> beam.io.Read(beam.io.BigQuerySource(query=last_revision_processed, validate=True, use_standard_sql=True)))
       # Read from ingested table to get last processed revision 
       page_state = (p | 'Retrieve_page_state' >> beam.io.Read(beam.io.BigQuerySource(query=last_page_state, validate=True)))
       # Read from page state table to get the page states recorded from previous processing steps
       mapping = (lambda x: (x['page_id'], x))

    reconstruction_results, page_states, last_rev, input_ps, input_rev = (to_be_processed 
                  | beam.Map(mapping) | beam.GroupByKey()
                  | beam.ParDo(ReconstructConversation(), last_revision=beam.pvalue.AsSingleton(last_revision), page_state=beam.pvalue.AsSingleton(page_state)).with_outputs('page_states', 'last_revision', 'input_page_state', 'to_be_processed_revision', main = 'reconstruction_results'))
                   # Reconstruct the conversations
    if known_args.save_res_to_cloud:
       page_states | "WritePageStates" >> beam.io.WriteToText("gs://wikidetox-viz-dataflow/%s/page_states"%jobname) 
       reconstruction_results | "WriteReconstructedResults" >> beam.io.WriteToText("gs://wikidetox-viz-dataflow/%s/reconstructed"%jobname) 
    else:
       page_states | "WritePageStates" >> beam.io.Write(bigquery_io.BigQuerySink(known_args.page_states_output_table, schema=known_args.page_states_output_schema, write_disposition='WRITE_APPEND', validate=True))
       reconstruction_results | "WriteReconstructedResults" >> beam.io.WriteToText("gs://wikidetox-viz-dataflow/results_%s/reconstructed%s"%(known_args.page_id, jobname)) 

       # Write the page states to BigQuery
#       reconstruction_results | "WriteReconstructedResults" >> beam.io.Write(bigquery_io.BigQuerySink(known_args.output_table, schema=known_args.output_schema, write_disposition='WRITE_APPEND', validate=True))
      # Write the reconstructed results to BigQuery
    if known_args.save_input_to_cloud_storage:
       last_rev | "WriteBackInput_last_rev" >> beam.io.WriteToText("gs://wikidetox-viz-dataflow/testing/%s.last_rev"%jobname)
       input_ps | "WriteBackInput_page_states" >> beam.io.WriteToText("gs://wikidetox-viz-dataflow/testing/%s.page_states"%jobname)
       input_rev | "WriteBackInput_input_revisions" >> beam.io.WriteToText("gs://wikidetox-viz-dataflow/testing/%s.input_revs"%jobname)

class ReconstructConversation(beam.DoFn):
  def merge(self, ps1, ps2):
       deleted_ids_ps2 = {d[1]:d for d in json.loads(ps2['deleted_comments'])}
       deleted_ids_ps1 = {d[1]:d for d in json.loads(ps1['deleted_comments'])}
       deleted_ids_ps2.update(deleted_ids_ps1)
       extra_ids = [key for key in deleted_ids_ps2.keys() if not(key in deleted_ids_ps1)]
       ret_p = copy.deepcopy(ps1)
       ret_p['deleted_comments'] = json.dumps(list(deleted_ids_ps2.values()))
       conv_ids = json.loads(ps2['conversation_id'])
       auth = json.loads(ps2['authors'])
       ret_p['conversation_id'] = json.loads(ret_p['conversation_id'])
       ret_p['authors'] = json.loads(ret_p['authors'])
       for i in extra_ids:
           ret_p['conversation_id'][i] = conv_ids[i] 
           ret_p['authors'][i] = auth[i]
       ret_p['conversation_id'] = json.dumps(ret_p['conversation_id'])
       ret_p['authors'] = json.dumps(ret_p['authors'])
       return ret_p
  def process(self, info, last_revision, page_state):
    (page_id, rows) = info
    if known_args.read_input_from_cloud:
       last_revision = json.loads(last_revision)
       page_state = json.loads(page_state)
    if rows == []: return 
    # Return when no revisions need to be processed for this page
    if page_id == None: return
    logging.info('USERLOG: Reconstruction work start on page: %s'%page_id)
    processor = Conversation_Constructor()
    if not(page_state) == []:
       if known_args.save_input_to_cloud_storage: 
          yield beam.pvalue.TaggedOutput('last_revision', json.dumps(last_revision))
          yield beam.pvalue.TaggedOutput('input_page_state', json.dumps(page_state))
       logging.info('Page %s existed: loading page state, last revision: %s'%(page_id, last_revision['rev_id'])) 
       processor.load(page_state['page_state'], page_state['deleted_comments'], page_state['conversation_id'], page_state['authors'], last_revision['text'])
    revision = {}
    last_revision = 'None'
    second_last_page_state = page_state 
    error_encountered = False
    cnt = 0
    last_loading = 0 
    rev_list = sorted(rows, key=lambda key: (key['timestamp'], key['rev_id_in_int']))
    for cur_revision in rev_list:
        if not('rev_id' in cur_revision): continue
        if cur_revision['record_index'] == 0: 
           revision = cur_revision
        else:
           revision['text'] += cur_revision['text']
        if cur_revision['record_index'] == cur_revision['records_count'] - 1:
           print(revision['timestamp'])
           cnt += 1
           last_revision = revision['rev_id']
           text = revision['text']
           if not(known_args.save_input_to_cloud_storage): 
              page_state, actions = processor.process(revision, DEBUGGING_MODE = False)
           else:
              actions = []
           last_page_state = copy.deepcopy(page_state)
           for action in actions:
               if known_args.save_res_to_cloud:
                  yield json.dumps(action)
               else:
                  yield action
           if known_args.save_input_to_cloud_storage: 
              yield beam.pvalue.TaggedOutput('to_be_processed_revision', json.dumps(cur_revision))
           if cnt % LOG_INTERVAL == 0 and cnt:
             # reload after every 200 revisions
              processor = Conversation_Constructor()
              second_last_page_state = copy.deepcopy(page_state)
              last_loading = cnt
              processor.load(page_state['page_state'], page_state['deleted_comments'], page_state['conversation_id'], page_state['authors'], text)
    if second_last_page_state and not(cnt == last_loading):
       last_page_state = self.merge(last_page_state, second_last_page_state)
    if last_page_state:
       if not(known_args.save_res_to_cloud):
          yield beam.pvalue.TaggedOutput('page_states', last_page_state)
       else:
          yield beam.pvalue.TaggedOutput('page_states', json.dumps(last_page_state))
    if not(error_encountered):
       logging.info('USERLOG: Reconstruction on page %s complete! last revision: %s' %(page_id, last_revision))


if __name__ == '__main__':
  logging.getLogger().setLevel(logging.INFO)
  parser = argparse.ArgumentParser()
  parser.add_argument('--save_res_to_cloud',
                      dest='save_res_to_cloud',
                      action='store_true',
                      help='Save the result to Cloud.')
  parser.add_argument('--save_input_to_cloud',
                      dest='save_input_to_cloud_storage',
                      action='store_true',
                      help='Save the inputs to Cloud.')
  parser.add_argument('--load_input_from_cloud',
                      dest='read_input_from_cloud',
                      action='store_true',
                      help='Read input from Cloud.')



  # Input BigQuery Table

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
  parser.add_argument('--page_states_output_schema',
                      dest='page_states_output_schema',
                      default=page_states_output_schema,
                      help='Page states output table schema.')
  output_schema = 'user_id:STRING, user_text:STRING, timestamp:STRING, content:STRING, parent_id:STRING, replyTo_id:STRING, indentation:INTEGER, page_id:STRING, page_title:STRING, type:STRING, id:STRING, rev_id:STRING, conversation_id:STRING, authors:STRING'  
  parser.add_argument('--output_schema',
                      dest='output_schema',
                      default=output_schema,
                      help='Output table schema.')
  parser.add_argument('--pageid',
                      dest='page_id',
                      help='The page_id you want to process')
  parser.add_argument('--week_step',
                      dest='week_step',
                      default=1,
                      help='Number of weeks you want to execute in one batch.')
 

  known_args, pipeline_args = parser.parse_known_args()
  known_args.input_table= 'wikidetox_conversations.ingested_super_long_%s'%(known_args.page_id)
  known_args.input_page_state_table= 'wikidetox_conversations.page_states_%s'%(known_args.page_id)
  known_args.page_states_output_table = 'wikidetox_conversations.page_states_%s'%(known_args.page_id) 
  known_args.output_table = 'wikidetox_conversations.reconstructed_%s'%(known_args.page_id) 
  if known_args.week:
     known_args.lower_week, known_args.upper_week = int(known_args.week), int(known_args.week)
     known_args.lower_year, known_args.upper_year = int(known_args.year), int(known_args.year)
  known_args.lower_week = int(known_args.lower_week)
  known_args.lower_year = int(known_args.lower_year) 
  known_args.upper_week = int(known_args.upper_week)
  known_args.upper_year = int(known_args.upper_year)
  known_args.week_step = int(known_args.week_step)
  lw = known_args.lower_week
  ly = known_args.lower_year
  uw = known_args.upper_week
  uy = known_args.upper_year
  known_args.upper_week = known_args.lower_week
  known_args.upper_year = known_args.lower_year


  if known_args.save_input_to_cloud_storage:
     known_args.save_res_to_cloud = True

  while ((known_args.lower_week <= uw and known_args.lower_year == uy) or known_args.lower_year < uy): 
      known_args.upper_week += known_args.week_step 
      if known_args.upper_week > 53:
         known_args.upper_year += int(known_args.upper_week/ 53)
         known_args.upper_week = known_args.upper_week % 53
         if not(known_args.upper_week):
            known_args.upper_week = 53

      if known_args.upper_year > uy or (known_args.upper_year == uy and known_args.upper_week > uw):
         known_args.upper_week = uw
         known_args.upper_year = uy
         print(known_args.lower_week, known_args.lower_year, known_args.upper_week, known_args.upper_year)
         run(known_args, pipeline_args)
         break
      print(known_args.lower_week, known_args.lower_year, known_args.upper_week, known_args.upper_year)
      run(known_args, pipeline_args)
      known_args.lower_week = known_args.upper_week + 1
      known_args.lower_year = known_args.upper_year
      if known_args.lower_week == 54: 
         known_args.lower_week = 1
         known_args.lower_year += 1
