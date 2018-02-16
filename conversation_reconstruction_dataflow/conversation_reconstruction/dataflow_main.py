
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
import copy
import sys

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import SetupOptions
from apache_beam.io.gcp import bigquery as bigquery_io 
from construct_utils.conversation_constructor import Conversation_Constructor


LOG_INTERVAL = 100

def run(known_args, pipeline_args):
  """Main entry point; defines and runs the reconstruction pipeline."""

  pipeline_args.extend([
    '--runner=DataflowRunner',
    '--project=wikidetox-viz',
    '--staging_location=gs://wikidetox-viz-dataflow/staging',
    '--temp_location=gs://wikidetox-viz-dataflow/tmp',
    '--job_name=reconstruction-from-{table}-week{lw}year{ly}-week{uw}year{uy}'.format(table=known_args.category, lw=known_args.lower_week, ly=known_args.lower_year, uw=known_args.upper_week, uy=known_args.upper_year),
    '--num_workers=30',
    '--extra_package=third_party/mwparserfromhell.tar.gz'
  ])
  pipeline_options = PipelineOptions(pipeline_args)
  pipeline_options.view_as(SetupOptions).save_main_session = True
  jobname = 'reconstruction-from-{table}-pages-week{lw}year{ly}-week{uw}year{uy}'.format(table=known_args.category, lw=known_args.lower_week, ly=known_args.lower_year, uw=known_args.upper_week, uy=known_args.upper_year)

  # Select the page_id you want to debug on, only works when reading from BigQuery
  debug_page =''#'and page_id = \'37130483\''
  debug1 =''#'where page_id = \'37130483\''

  # Queries extracting the data
  within_time_range = '((week >= {lw} and year = {ly}) or year > {ly}) and ((week <= {uw} and year = {uy}) or year < {uy})'.format(lw = known_args.lower_week, ly = known_args.lower_year, uw = known_args.upper_week, uy = known_args.upper_year)
  before_time_range = '(week < {lw} and year = {ly}) or year < {ly}'.format(lw=known_args.lower_week, ly=known_args.lower_year) 
  ingested_revs_for_processing = "WITH revs AS (SELECT * FROM {input_table} WHERE {time_range} {debug}) SELECT page_id, ARRAY_AGG(revs) AS cur_rev FROM revs GROUP BY page_id".format(input_table=known_args.input_table, time_range=within_time_range, debug=debug_page)
  last_revision_processed = "WITH revs AS (SELECT * FROM {input_table} WHERE {before_time_range} {debug}) SELECT page_id, ARRAY_AGG(revs ORDER BY timestamp DESC, rev_id_in_int DESC LIMIT 1)[OFFSET(0)] AS last_rev FROM revs GROUP BY page_id".format(input_table=known_args.last_revision_table, before_time_range=before_time_range, debug=debug_page)
  last_page_state = "WITH page_states AS (SELECT * FROM {page_state_table} {debug}) SELECT page_id, ARRAY_AGG(page_states ORDER BY timestamp DESC, rev_id DESC LIMIT 1)[OFFSET(0)] AS last_page_state FROM page_states GROUP BY page_id".format(page_state_table=known_args.input_page_state_table, debug=debug1)
  groupby_mapping = lambda x: (x['page_id'], x)
  with beam.Pipeline(options=pipeline_options) as p:
    if known_args.read_input_from_cloud:
       # Read Input From Cloud
       groupby_mapping = lambda x: (json.loads(x)['page_id'], json.loads(x))
       to_be_processed = (p | 'Read_to_be_processed' >> beam.io.ReadFromText("gs://wikidetox-viz-dataflow/testing/%s.input_revs*"%jobname)| 'INGESTED_assign_page_id_as_key' >> beam.Map(groupby_mapping))
       last_revision = (p | 'Retrieve_last_revision' >> beam.io.ReadFromText("gs://wikidetox-viz-dataflow/testing/%s.last_rev*"%jobname)| 'LASTREV_assign_page_id_as_key' >> beam.Map(groupby_mapping))
       page_state = (p | 'Retrieve_page_state' >> beam.io.ReadFromText("gs://wikidetox-viz-dataflow/testing/%s.page_states*"%jobname)| 'PAGESTATE_assign_page_id_as_key' >> beam.Map(groupby_mapping))
    else:
       # Read from BigQuery
       to_be_processed = (p | 'Read_to_be_processed' >> beam.io.Read(beam.io.BigQuerySource(query=ingested_revs_for_processing, validate=True, use_standard_sql=True))
                            | 'INGESTED_assign_page_id_as_key' >> beam.Map(groupby_mapping))
       last_revision = (p 
            | 'Retrieve_last_revision' >> beam.io.Read(beam.io.BigQuerySource(query=last_revision_processed, validate=True, use_standard_sql=True))
            | 'LASTREV_assign_page_id_as_key' >> beam.Map(groupby_mapping))
       page_state = (p | 'Retrieve_page_state' >> beam.io.Read(beam.io.BigQuerySource(query=last_page_state, validate=True, use_standard_sql=True))
                       | 'PAGESTATE_assign_page_id_as_key' >> beam.Map(groupby_mapping))

    reconstruction_results, page_states, last_rev, last_rev_output, input_ps, input_rev\
                   = ({'to_be_processed': to_be_processed, 'last_revision': last_revision, 'page_state': page_state}
                   | beam.CoGroupByKey()
                   # Join information based on page_id
                   | beam.ParDo(ReconstructConversation()).with_outputs('page_states', 'last_revision', 'last_revision_output', 'input_page_state', 'to_be_processed_revision', main = 'reconstruction_results'))
                   # Reconstruct the conversations
 
    if known_args.save_res_to_cloud:
       # Saving result to cloud storage
       page_states | "WritePageStates" >> beam.io.WriteToText("gs://wikidetox-viz-dataflow/%s/page_states"%jobname) 
       reconstruction_results | "WriteReconstructedResults" >> beam.io.WriteToText("gs://wikidetox-viz-dataflow/reconstructed_res/%s"%jobname) 
       last_rev_output | "WriteCollectedLastRevision" >> beam.io.WriteToText("gs://wikidetox-viz-dataflow/%s/last_rev"%jobname)
 
    else:
       # Saving page states and last processed revision to BigQuery, and the last time last processed revision to cloud for bak up
       page_states | "WritePageStates" >> beam.io.Write(bigquery_io.BigQuerySink(known_args.page_states_output_table, schema=known_args.page_states_output_schema, write_disposition='WRITE_APPEND', validate=True))
       reconstruction_results | "WriteReconstructedResults" >> beam.io.WriteToText("gs://wikidetox-viz-dataflow/short_pages/reconstructed_%s"%jobname) 
#       last_rev_output | "WriteCollectedLastRevision" >> beam.io.Write(bigquery_io.BigQuerySink(known_args.last_revision_table, schema=known_args.ingested_revision_schema, write_disposition='WRITE_TRUNCATE', validate=True))
       last_rev | "WriteBackInput_last_rev" >> beam.io.WriteToText("gs://wikidetox-viz-dataflow/bakup/%s.last_rev"%jobname)

    if known_args.save_input_to_cloud_storage:
       # Write input data to cloud to save cost on testing
       input_rev | "WriteBackInput_revs" >> beam.io.WriteToText("gs://wikidetox-viz-dataflow/testing/%s.input_revs"%jobname) 
       last_rev | "WriteBackInput_last_rev" >> beam.io.WriteToText("gs://wikidetox-viz-dataflow/testing/%s.last_rev"%jobname)
       input_ps | "WriteBackInput_page_states" >> beam.io.WriteToText("gs://wikidetox-viz-dataflow/testing/%s.page_states"%jobname)

class ReconstructConversation(beam.DoFn):
  def merge(self, ps1, ps2):
       # Merge two page states, ps1 is the later one
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

  def process(self, info):
    (page_id, data) = info
    if page_id == None: return

    if known_args.read_input_from_cloud:
       # Load input from cloud(the format is different here)
       rows = data['to_be_processed']
       last_revision = data['last_revision']
       page_state = data['page_state']
       fields = ['rev_id_in_int', 'week', 'year', 'records_count', 'record_index']
       if not(page_state == []):
          last_revision = last_revision[0]
          page_state = page_state[0]
          page_state['rev_id'] = int(page_state['rev_id'])
          for f in fields:
              last_revision[f] = int(last_revision[f])
          last_revision['truncated'] = bool(last_revision['truncated'])

       # Also the types were not preserved

       for r in rows:
           for f in fields:
               r[f] = int(r[f])
           r['truncated'] = bool(r['truncated'])
    else:
       if data['to_be_processed'] == []: 
          rows = []
       else:
          rows = data['to_be_processed'][0]['cur_rev']
       if data['last_revision'] == []:
          last_revision = []
       else:
          last_revision = data['last_revision'][0]['last_rev']
       if not(data['page_state'] == []):
          page_state = data['page_state'][0]['last_page_state']
       else:
          page_state = []
       # Return when no revisions need to be processed for this page
       if not(rows == []) and 'Archive' in rows[0]['page_title']: return 
    page_state = []
    if rows == []:
       if not(last_revision == []): #not(known_args.save_res_to_cloud) and 
          yield beam.pvalue.TaggedOutput('last_revision_output', last_revision)
          yield beam.pvalue.TaggedOutput('last_revision', json.dumps(last_revision))
       return

    logging.info('USERLOG: Reconstruction work start on page: %s'%page_id)
    processor = Conversation_Constructor()
    last_revision_to_save = last_revision
    if not(page_state) == []:
       # Write the input to cloud
       yield beam.pvalue.TaggedOutput('last_revision', json.dumps(last_revision))
       yield beam.pvalue.TaggedOutput('input_page_state', json.dumps(page_state))
       logging.info('Page %s existed: loading page state, last revision: %s'%(page_id, last_revision['rev_id'])) 
       # Load previous page state
       processor.load(page_state['page_state'], page_state['deleted_comments'], page_state['conversation_id'], page_state['authors'], last_revision['text'])

    revision = {}
    last_revision = 'None'
    second_last_page_state = page_state 
    error_encountered = False
    cnt = 0
    revision_lst = sorted([r for r in rows], key=lambda k: (k['timestamp'], k['rev_id_in_int'], k['record_index']))
    # Sort by temporal order
    last_loading = 0
    last_page_state = page_state 
    for cur_revision in revision_lst:
        # Process revision by revision 
        if not('rev_id' in cur_revision): continue
        if cur_revision['record_index'] == 0: 
           revision = cur_revision
        else:
           revision['text'] += cur_revision['text']
        if cur_revision['record_index'] == cur_revision['records_count'] - 1:
           cnt += 1
           last_revision = revision['rev_id']
           last_revision_to_save = copy.deepcopy(revision)
           text = revision['text']
           # If the saving option was set, no processing will be done
           if not(known_args.save_input_to_cloud_storage): 
              page_state, actions = processor.process(revision, DEBUGGING_MODE = False)
           else:
              actions = []
           last_page_state = copy.deepcopy(page_state)
           for action in actions:
               yield json.dumps(action)
           if known_args.save_input_to_cloud_storage: 
              yield beam.pvalue.TaggedOutput('to_be_processed_revision', json.dumps(cur_revision))
           if cnt % LOG_INTERVAL == 0 and cnt and not(page_state == []):
             # reload after every 200 revisions to keep the memory low
              processor = Conversation_Constructor()
              second_last_page_state = copy.deepcopy(page_state)
              last_loading = cnt
              processor.load(page_state['page_state'], page_state['deleted_comments'], page_state['conversation_id'], page_state['authors'], text)
    if second_last_page_state and not(cnt == last_loading):
       # Merge the last two page states
       last_page_state = self.merge(last_page_state, second_last_page_state)
    if last_page_state and not(last_page_state == []):
       size = sys.getsizeof(last_page_state)
       if size > 10485760:
          # Send error if the page state gets too big
          logging.error('Row size limit exceeded: size %d, page id %s'%(size, page_id))
       if not(known_args.save_res_to_cloud):
          yield beam.pvalue.TaggedOutput('page_states', last_page_state)
       else:
          yield beam.pvalue.TaggedOutput('page_states', json.dumps(last_page_state))
    if not(last_revision_to_save == []): #not(known_args.save_res_to_cloud) and 
       yield beam.pvalue.TaggedOutput('last_revision_output', last_revision_to_save)
    if not(error_encountered):
       logging.info('USERLOG: Reconstruction on page %s complete! last revision: %s' %(page_id, last_revision))

if __name__ == '__main__':
  logging.getLogger().setLevel(logging.INFO)
  parser = argparse.ArgumentParser()
  # Running Options 
  parser.add_argument('--save_res_to_cloud',
                      dest='save_res_to_cloud',
                      action='store_true',
                      help='Save the result to Cloud.')
  parser.add_argument('--save_input_to_cloud',
                      dest='save_input_to_cloud_storage',
                      action='store_true',
                      help='Save the inputs and result to Cloud, no processing will be run at this stage.')
  parser.add_argument('--load_input_from_cloud',
                      dest='read_input_from_cloud',
                      action='store_true',
                      help='Read input from Cloud.')

  # Input/Output parameters
  parser.add_argument('--category',
                      dest='category',
                      help='Specify the job category: long (pages), short (pages),test.')

  parser.add_argument('--input_table',
                      dest='input_table',
                      help='Input table with ingested revisions.')
  parser.add_argument('--input_page_state_table',
                      dest='input_page_state_table',
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
  parser.add_argument('--last_revision_table',
                      dest='last_revision_table',
                      default=None,
                      help='The table you want to store and read from for the last revision being processed.')
  parser.add_argument('--page_states_output_table',
                      dest='page_states_output_table',
                      help='Output page state table for reconstruction.')
  parser.add_argument('--week_step',
                      dest='week_step',
                      default=1,
                      help='Number of weeks you want to execute in one batch.')

  known_args, pipeline_args = parser.parse_known_args()
  known_args.ingested_revision_schema = 'sha1:STRING,user_id:STRING,format:STRING,user_text:STRING,timestamp:STRING,text:STRING,page_title:STRING,model:STRING,page_namespace:STRING,page_id:STRING,rev_id:STRING,comment:STRING,user_ip:STRING,truncated:BOOLEAN,records_count:INTEGER,record_index:INTEGER,week:INTEGER,year:INTEGER,rev_id_in_int:INTEGER'
  known_args.output_schema = 'user_id:STRING,user_text:STRING,timestamp:STRING,content:STRING,parent_id:STRING,replyTo_id:STRING,indentation:INTEGER,page_id:STRING,page_title:STRING,type:STRING,id:STRING,rev_id:STRING,conversation_id:STRING,authors:STRING'  
  known_args.page_states_output_schema = 'rev_id:INTEGER,page_id:STRING,page_state:STRING,deleted_comments:STRING,conversation_id:STRING,authors:STRING,timestamp:STRING'  
  # If only one week was specified 
  if known_args.week:
     known_args.lower_week, known_args.upper_week = int(known_args.week), int(known_args.week)
  # If only one year was specified 
  if known_args.year:
     known_args.lower_year, known_args.upper_year = int(known_args.year), int(known_args.year)
  # Change the parameters to integers
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

  # If the save_input_to_cloud_storage option is set the result will be saved to cloud as well
  if known_args.save_input_to_cloud_storage:
     known_args.save_res_to_cloud = True

  # Iterate from the lower (week, year) to the upper (week, year) using week step
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
      # Run the processing pipeline
      run(known_args, pipeline_args)
      known_args.lower_week = known_args.upper_week + 1
      known_args.lower_year = known_args.upper_year
      if known_args.lower_week == 54: 
         known_args.lower_week = 1
