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

Run Constructor

Runs wikipedia_revisions_constructor.py with command line arguments for input.
"""

# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import xml.sax
import subprocess
import argparse
from os import path
from google.cloud import bigquery as bigquery_op
import json
from .conversation_constructor import Conversation_Constructor

parser = argparse.ArgumentParser(description='Running conversation reconstruction on a list of revisions.')
parser.add_argument('--revisions',  dest='revision_ids', required = True, help='A revision list in json format for reconstruction.')
parser.add_argument('--table',  dest='table', required = True, help='BigQeury table where the revisions are stored.')
args = parser.parse_args()
UPDATE_RATE = 200

def QueryResult2json(queryresults): 
    ret = {}
    fields = ['sha1', 'user_id', 'format', 'user_text', 'timestamp', 'text', 'page_title',\
    'model', 'page_namespace', 'page_id', 'rev_id', 'comment', 'user_ip', 'truncated', 'record_count', 'record_index']
    for ind, val in enumerate(queryresults): 
        ret[fields[ind]] = val
    return ret

def run(revision_ids, table):
  page_history = []
  client = bigquery_op.Client(project='wikidetox-viz')
  processor = Conversation_Constructor()
  for ind, rev_id in enumerate(revision_ids):
      query = ("select * from %s where rev_id=\"%s\""%(table, rev_id))
      ret = client.run_sync_query(query)
      ret.run()
      revision = {}
      for row in ret.rows:
          revision = QueryResult2json(row)
      actions = processor.process(revision, DEBUGGING_MODE = False)
      for action in actions:
          print(json.dumps(action))
  return processor.page

if __name__ == '__main__':
  run(json.loads(args.revision_ids), args.table)

