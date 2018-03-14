
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
import ast
from google.cloud import bigquery as bigquery_op 
import copy
import sys

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import SetupOptions
from apache_beam.io.avroio import ReadFromAvro 
from construct_utils.conversation_constructor import Conversation_Constructor


LOG_INTERVAL = 100

def run(known_args, pipeline_args):
  """Main entry point; defines and runs the reconstruction pipeline."""

  pipeline_args.extend([
    '--runner=DataflowRunner',
    '--project=wikidetox-viz',
    '--staging_location=gs://wikidetox-viz-dataflow/staging',
    '--temp_location=gs://wikidetox-viz-dataflow/tmp',
    '--job_name=reconstruction-from-{table}-week{lw}year{ly}'.format(table=known_args.category, lw=known_args.week, ly=known_args.year),
    '--num_workers=30',
    '--extra_package=third_party/mwparserfromhell.tar.gz'
  ])
  pipeline_options = PipelineOptions(pipeline_args)
  pipeline_options.view_as(SetupOptions).save_main_session = True
  jobname = 'reconstruction-from-{table}-pages-week{lw}year{ly}'.format(table=known_args.category, lw=known_args.week, ly=known_args.year)
  print(known_args.input.format(week=known_args.week, year=known_args.year))

  avro_mapping = lambda x: (x['page_id'], x)
  json_mapping_tmp = lambda x: (x[0]["page_id"], x[0]) if (type(x[0]) is dict) else ((ast.literal_eval(x)["page_id"], ast.literal_eval(x)) if (type(ast.literal_eval(x)) is dict) else (ast.literal_eval(x)[0]["page_id"], ast.literal_eval(x)[0]))
  json_mapping = lambda x: (json.loads(x)["page_id"], json.loads(x))
  with beam.Pipeline(options=pipeline_options) as p:
   # Read from BigQuery
    to_be_processed = (p | 'Read_to_be_processed' >> beam.io.ReadFromAvro(known_args.input.format(week=known_args.week, year=known_args.year))
                          | 'INGESTED_assign_page_id_as_key' >> beam.Map(avro_mapping))
    last_revision = (p | 'Retrieve_last_revision' >> beam.io.ReadFromText("gs://wikidetox-viz-dataflow/process_tmp/%s/*last_rev*"%known_args.category)| 'LASTREV_assign_page_id_as_key' >> beam.Map(json_mapping))
    page_state = (p | 'Retrieve_page_state' >> beam.io.ReadFromText("gs://wikidetox-viz-dataflow/process_tmp/%s/*page_states*"%known_args.category)| 'PAGESTATE_assign_page_id_as_key' >> beam.Map(json_mapping))

    reconstruction_results, page_states, input_last_rev, last_rev_output, input_page_states\
                   = ({'to_be_processed': to_be_processed, 'last_revision': last_revision, 'page_state': page_state}
                   | beam.CoGroupByKey()
                   # Join information based on page_id
                   | beam.ParDo(ReconstructConversation()).with_outputs('page_states', 'last_revision', 'last_revision_output', 'input_page_state', main = 'reconstruction_results'))
                   # Reconstruct the conversations
 
    page_states | "WritePageStates" >> beam.io.WriteToText("gs://wikidetox-viz-dataflow/process_tmp/next_%s/page_states"%known_args.category) 
    # Saving page states and last processed revision to BigQuery, and the last time last processed revision to cloud for bak up
    reconstruction_results | "WriteReconstructedResults" >> beam.io.WriteToText("gs://wikidetox-viz-dataflow/reconstructed_res/%s"%jobname) 
    last_rev_output | "WriteCollectedLastRevision" >> beam.io.WriteToText("gs://wikidetox-viz-dataflow/process_tmp/next_%s/last_rev"%known_args.category)
    input_last_rev | "WriteBackInput_last_rev" >> beam.io.WriteToText("gs://wikidetox-viz-dataflow/bakup/%s/last_rev"%jobname)
    input_page_states | "WriteBackInput_page_states" >> beam.io.WriteToText("gs://wikidetox-viz-dataflow/bakup/%s/page_states"%jobname)

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
    if (page_id == None): return

    # Load input from cloud(the format is different here)
    rows = data['to_be_processed']
    last_revision = data['last_revision']
    page_state = data['page_state']
    # Clean type formatting
    fields = ['rev_id_in_int', 'week', 'year', 'records_count', 'record_index']
    if not(last_revision == []):
       for ind in range(len(last_revision)):
           last_revision[ind]['rev_id_in_int'] = int(last_revision[ind]['rev_id_in_int'])
       last_revision = sorted(last_revision, key=lambda x : x['rev_id_in_int'])
       last_revision = last_revision[-1]
       for f in fields:
           last_revision[f] = int(last_revision[f])
       last_revision['truncated'] = bool(last_revision['truncated'])
    else:
       last_revision = None
    if not(page_state == []):
       for ind in range(len(page_state)):
           page_state[ind]['rev_id'] = int(page_state[ind]['rev_id'])
       page_state = sorted(page_state, key=lambda x : x['rev_id'])
       page_state = page_state[-1]
    else:
       page_state = None

    for r in rows:
        for f in fields:
            r[f] = int(r[f])
        r['truncated'] = bool(r['truncated'])
    # Ignore Archive pages 
    if not(rows == []) and 'Archive' in rows[0]['page_title']: return 

    # Return when no pages to be processed
    if rows == []:
       if not(last_revision == None): 
          yield beam.pvalue.TaggedOutput('last_revision_output', json.dumps(last_revision))
          yield beam.pvalue.TaggedOutput('last_revision', json.dumps(last_revision))
       if not(page_state == None): 
          yield beam.pvalue.TaggedOutput('input_page_state', json.dumps(page_state))
          yield beam.pvalue.TaggedOutput('page_states', json.dumps(page_state))
       return

    logging.info('USERLOG: Reconstruction work start on page: %s'%page_id)
    processor = Conversation_Constructor()
    last_revision_to_save = last_revision
    if not(page_state == None):
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
           page_state, actions = processor.process(revision, DEBUGGING_MODE = False)
           last_page_state = copy.deepcopy(page_state)
           for action in actions:
               yield json.dumps(action)
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
       yield beam.pvalue.TaggedOutput('page_states', json.dumps(last_page_state))
    if not(last_revision_to_save == []): 
       yield beam.pvalue.TaggedOutput('last_revision_output', json.dumps(last_revision_to_save))
    if not(error_encountered):
       logging.info('USERLOG: Reconstruction on page %s complete! last revision: %s' %(page_id, last_revision))

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
  parser.add_argument('--week',
                      dest='week',
                      default=1,
                      help='The week of data you want to process')
  parser.add_argument('--year',
                      dest='year',
                      default=None,
                      help='The year that the week is in')
  known_args, pipeline_args = parser.parse_known_args()
  run(known_args, pipeline_args)

