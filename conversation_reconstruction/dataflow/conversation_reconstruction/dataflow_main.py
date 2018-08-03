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

reconstruct*.sh in helper_shell

"""
from __future__ import absolute_import
import argparse
import logging
import traceback
import subprocess
import resource
import json
import os
from os import path
import urllib2
import tempfile
import ast
import copy
import sys
import time

import apache_beam as beam
from apache_beam.io import filesystems
from apache_beam.metrics.metric import Metrics
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import SetupOptions
from construct_utils.conversation_constructor import Conversation_Constructor


LOG_INTERVAL = 100
MEMORY_THERESHOLD = 1000000
REVISION_THERESHOLD = 250000000
SAVE_TO_MEMORY = 0
SAVE_TO_STORAGE = 1
RETRY_LIMIT = 10

def get_metadata(x):
  record_size = len(x)
  record = json.loads(x)
  return (record['page_id'], {'page_id': record['page_id'], 'rev_id': record['rev_id'],
                              'timestamp': record['timestamp'], 'record_size': record_size})


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
    '--job_name=reconstruction-{}'.format(known_args.output_name),
    '--num_workers=80'
  ])
  pipeline_options = PipelineOptions(pipeline_args)
  pipeline_options.view_as(SetupOptions).save_main_session = True
  jobname = 'reconstruction-pages-{}'.format(known_args.output_name)

  json_mapping = lambda x: (json.loads(x)["page_id"], json.loads(x))
  with beam.Pipeline(options=pipeline_options) as p:
    # Identify Input Locations
    revision_location = known_args.input
    tmp_input = "gs://wikidetox-viz-dataflow/%s/revs/" % known_args.process_file
    last_revision_location = "gs://wikidetox-viz-dataflow/%s/current/last_rev*" % known_args.process_file
    page_state_location = "gs://wikidetox-viz-dataflow/%s/current/page_states*" % known_args.process_file
    error_log_location = "gs://wikidetox-viz-dataflow/%s/current/error_log*" % known_args.process_file

    # Read from Cloud Storage
    revision_metadata = (p | 'ReadRevisionMetadata' >> beam.io.ReadFromText(revision_location)
                         | 'MapToMetaData' >> beam.Map(lambda x: get_metadata(x))
                         | beam.GroupByKey()
                         | beam.ParDo(Count()))
    raw_revisions = (p | 'ReadRawRevisions' >> beam.io.ReadFromText(revision_location)
                       | 'assign_rev_id_as_key' >>beam.Map(lambda x: (json.loads(x)['rev_id'], x)))
    to_be_processed = ({'metadata': revision_metadata, 'raw': raw_revisions}
                       | 'GroupbyRevID' >> beam.CoGroupByKey()
                       | 'WriteToStroage' >> beam.ParDo(WriteToStorage(), tmp_input))

    last_revision = (p | 'Retrieve_last_revision' >> beam.io.ReadFromText(last_revision_location)
                       | 'LASTREV_assign_page_id_as_key' >> beam.Map(json_mapping))
    page_state = (p | 'Retrieve_page_state' >> beam.io.ReadFromText(page_state_location)
                    | 'PAGESTATE_assign_page_id_as_key' >> beam.Map(json_mapping))
    error_log = (p | 'Retrieve_error_log' >> beam.io.ReadFromText(error_log_location)
                    | 'ERRORLOG_assign_page_id_as_key' >> beam.Map(json_mapping))

    # Main Pipeline
    reconstruction_results, page_states, last_rev_output, error_log\
                   = ({'to_be_processed': to_be_processed, 'last_revision': last_revision, \
                       'page_state': page_state, 'error_log': error_log}
                   # Join information based on page_id.
                   | 'GroupBy_page_id' >> beam.CoGroupByKey()
                   | beam.ParDo(ReconstructConversation(), tmp_input).with_outputs('page_states',\
                               'last_revision','error_log',  main = 'reconstruction_results'))
    # Main Result
    reconstruction_results | "WriteReconstructedResults" >> beam.io.WriteToText("gs://wikidetox-viz-dataflow/reconstructed_res/%s/revisions-" % jobname)

    # Saving intermediate results to separate locations.
    folder = "gs://wikidetox-viz-dataflow/%s/next_stage/" % known_args.process_file
    page_states | "WritePageStates" >> beam.io.WriteToText(folder + "page_states")
    last_rev_output | "WriteCollectedLastRevision" >> beam.io.WriteToText(folder + "last_rev")
    error_log | "WriteErrorLog" >> beam.io.WriteToText(folder + "error_log")


class Count(beam.DoFn):
  def __init__(self):
      self.pages_to_storage = Metrics.counter(self.__class__, 'pages_to_storage')
      self.pages = Metrics.counter(self.__class__, 'pages')

  def process(self, element):
    (page_id, metadata) = element
    flag = SAVE_TO_MEMORY
    revision_sum = 0
    self.pages.inc()
    metadata = list(metadata)
    for s in metadata:
      revision_sum += s['record_size']
      if revision_sum > REVISION_THERESHOLD:
         flag = SAVE_TO_STORAGE
         self.pages_to_storage.inc()
         break
    for rev in metadata:
      yield (rev['rev_id'], flag)


class WriteToStorage(beam.DoFn):
  def __init__(self):
      self.revisions_to_storage = Metrics.counter(self.__class__, 'revisions_to_storage')
      self.write_retries = Metrics.counter(self.__class__, 'write_retries')

  def process(self, element, outputdir):
    (rev_id, data) = element
    metadata = data['metadata'][0]
    raw = data['raw'][0]
    if metadata == SAVE_TO_MEMORY:
      logging.info("USERLOG: Write to memory.")
      ret = json.loads(raw)
      page_id = ret['page_id']
      ret['rev_id'] = int(ret['rev_id'])
    else:
      element = json.loads(raw)
      page_id = element['page_id']
      rev_id = element['rev_id']
      self.revisions_to_storage.inc()
      # Creates writing path given the week, year pair
      write_path = path.join(outputdir, page_id, rev_id)
      # Writes to storage
      logging.info('USERLOG: Write to path %s.' % write_path)
      wait_time = 1
      for i in range(RETRY_LIMIT):
          try:
             with filesystems.FileSystems.create(write_path) as outputfile:
                json.dump(element, outputfile)
          except RuntimeError:
            self.write_retries.inc()
            time.sleep(wait_time)
            wait_time *= 2
          else:
            break
      ret = {'timestamp': element['timestamp'], 'rev_id': int(rev_id)}
    yield (page_id, ret)


class ReconstructConversation(beam.DoFn):
  def merge(self, ps1, ps2):
       # Merge two page states, ps1 is the later one
       deleted_ids_ps2 = {d[1]:d for d in ps2['deleted_comments']}
       deleted_ids_ps1 = {d[1]:d for d in ps1['deleted_comments']}
       deleted_ids_ps2.update(deleted_ids_ps1)
       extra_ids = [key for key in deleted_ids_ps2.keys() if key not in deleted_ids_ps1]
       ret_p = copy.deepcopy(ps1)
       ret_p['deleted_comments'] = list(deleted_ids_ps2.values())
       conv_ids = ps2['conversation_id']
       auth = ps2['authors']
       ret_p['conversation_id'] = ret_p['conversation_id']
       ret_p['authors'] = ret_p['authors']
       for i in extra_ids:
           ret_p['conversation_id'][i] = conv_ids[i]
           ret_p['authors'][i] = auth[i]
       ret_p['conversation_id'] = ret_p['conversation_id']
       ret_p['authors'] = ret_p['authors']
       return ret_p

  def process(self, info, tmp_input):
    (page_id, data) = info
    if (page_id == None): return
    logging.info('USERLOG: Reconstruction work start on page: %s' % page_id)
    # Load input from cloud
    last_revision = data['last_revision']
    page_state = data['page_state']
    error_log = data['error_log']
    # Clean type formatting
    if last_revision != []:
       assert(len(last_revision) == 1)
       last_revision = last_revision[0]
    else:
       last_revision = None
    if page_state != []:
       assert(len(page_state) == 1)
       page_state = page_state[0]
       page_state['page_state']['actions'] = \
           {int(pos) : tuple(val) for pos, val in page_state['page_state']['actions'].iteritems()}
       page_state['authors'] = \
           {action_id: [tuple(author) for author in authors] \
            for action_id, authors in page_state['authors'].iteritems()}
    else:
       page_state = None
    if error_log != []:
       assert(len(error_log) == 1)
       error_log = error_log[0]
    else:
       error_log = None
    rev_ids = []
    rev_ids = data['to_be_processed']
    # Return when the page doesn't have updates to be processed
    if len(rev_ids) == 0  or (error_log and
                              error_log['rev_id'] <= min(r['rev_id'] for r in rev_ids)):
       assert((last_revision and page_state) or \
              ((last_revision is None) and (page_state is None)))
       if last_revision:
          yield beam.pvalue.TaggedOutput('last_revision', json.dumps(last_revision))
          yield beam.pvalue.TaggedOutput('page_states', json.dumps(page_state))
       if error_log:
          yield beam.pvalue.TaggedOutput('error_log', json.dumps(error_log))
       logging.info('Page %s has no sufficient input in this time period.' % (page_id))
       return

    processor = Conversation_Constructor()
    if page_state:
       logging.info('Page %s existed: loading page state.' % (page_id))
       # Load previous page state.
       processor.load(page_state['deleted_comments'])
       latest_content = last_revision['text']
    else:
       latest_content = ""

    # Initialize
    last_revision_id = 'None'
    page_state_bak = None
    cnt = 0
    # Sort revisions by temporal order.
    revision_lst = sorted(rev_ids, key=lambda x: (x['timestamp'], x['rev_id']))
    last_loading = 0
    logging.info('Reconstruction on page %s started.' % (page_id))
    if 'text' not in revision_lst[0]:
      tempfile_path = tempfile.mkdtemp()
      os.system("gsutil -m cp -r %s %s" % (path.join(tmp_input, page_id), tempfile_path + '/'))
    for key in revision_lst:
        if 'text' not in key:
           with open(path.join(tempfile_path, page_id, str(key['rev_id'])), 'r') as f:
              revision = json.load(f)
           os.system("rm %s" % path.join(tempfile_path, page_id, str(key['rev_id'])))
        else:
           revision = key
        revision['rev_id'] = int(revision['rev_id'])
        # Process revision by revision.
        if 'rev_id' not in revision: continue
        cnt += 1
        last_revision_id = revision['rev_id']
        if revision['text'] == None: revision['text'] = ""
        logging.debug("REVISION CONTENT: %s" % revision['text'])
        try:
           page_state, actions, latest_content = \
               processor.process(page_state, latest_content, revision)
        except AssertionError:
           yield beam.pvalue.TaggedOutput('error_log', \
                      json.dumps({'page_id': page_id, 'rev_id': last_revision_id}))
           break

        for action in actions:
            yield json.dumps(action)
        memory_used = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        if memory_used >= MEMORY_THERESHOLD:
          logging.info("MEMORY USED MORE THAN THERESHOLD in PAGE %s REVISION %d : %d KB" % (revision['page_id'], revision['rev_id'], memory_used))
        if (cnt % LOG_INTERVAL == 0 and cnt) and page_state:
          # Reload after every LOG_INTERVAL revisions to keep the low memory
          # usage.
           processor = Conversation_Constructor()
           page_state_bak = copy.deepcopy(page_state)
           last_loading = cnt
           processor.load(page_state['deleted_comments'])
           page_state['deleted_comments'] = []
        revision = None
    if page_state_bak and cnt != last_loading:
       # Merge the last two page states if a reload happens while processing,
       # otherwise in a situation where a week's data contains LOG_INTERVAL + 1
       # revisions, the page state may only contain data from one revision.
       page_state = self.merge(page_state, page_state_bak)
    if error_log:
       yield beam.pvalue.TaggedOutput('error_log', json.dumps(error_log))
    yield beam.pvalue.TaggedOutput('page_states', json.dumps(page_state))
    yield beam.pvalue.TaggedOutput('last_revision', json.dumps({'page_id': page_id, 'text': latest_content}))
    logging.info('USERLOG: Reconstruction on page %s complete! last revision: %s' % (page_id, last_revision_id))

if __name__ == '__main__':
#  logging.basicConfig(filename="debug.log", level=logging.INFO)
  logging.getLogger().setLevel(logging.INFO)
  parser = argparse.ArgumentParser()
  # input/output parameters.
  parser.add_argument('--input',
                      dest='input',
                      help='input storage.')
  parser.add_argument('--output_name',
                      dest='output_name',
                      default=1,
                      help='Name of the result file.')
  parser.add_argument('--process_file',
                      dest='process_file',
                      default='process_tmp',
                      help='Cloud storage for intermediate processing file.')
  parser.add_argument('--testmode',
                      dest='testmode',
                      action='store_true',
                      help='Wheather to run in testmode.')

  known_args, pipeline_args = parser.parse_known_args()
  run(known_args, pipeline_args)

