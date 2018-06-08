# -*- coding: utf-8 -*-
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

A helper-tool for testing the reconstruction process that collects revisions of
given pages and stores them in testdata.

Note that the written records will be in descending order in terms of timestamp,
in order to be used as testdata in tester, please use $ tac FILE > OUTFILE$ or
$ sh reverse_order.sh $ in testdata/.

Run with default page id list:
python fetch_testdata.py

Or:
  python fetch_testdata.py -p PAGE_ID_LIST

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
import copy
import sys
import time
import requests
import argparse

default_page_ids = [34948919, 15854766, 32094486, 43758735, 22811813, 9373474, 28031]

def rename(record, page_id):
   record['rev_id'] = record['revid']
   del record['revid']
   record['user_text'] = record['user']
   del record['user']
   record['user_id'] = record['userid']
   del record['userid']
   record['text'] = record['*']
   del record['*']
   record['page_id'] = page_id

   # These fields are not used in testcases also not included in the Wikipedia
   # API but might be useful in downstream applications. Thus here we use a
   # placeholder value to ensure the same format of the input data in testing and
   # running and reduce the complexity of testdata collection.
   for entry in ['format', 'model', 'user_ip', 'page_title', 'page_namespace']:
       record[entry] = 'placeholder'
   return record

def get_revision(page_id):
  """Queries Wikipedia API for revision data given the page id."""
  baseurl = 'http://en.wikipedia.org/w/api.php'
  props = ['ids', 'timestamp', 'user', 'userid', 'sha1', 'comment', 'content']
  atts = {'action' : 'query',  'prop' : 'revisions', 'rvprop' : '|'.join(props), 'rvlimit' : 'max', 'format' : 'json', 'pageids' : page_id}
  while True:
     response = requests.get(baseurl, params = atts)
     if response.status_code != 429:
        break
     time.sleep(10)
  data = response.json()
  cnt = 0
  for page, val in data['query']['pages'].items():
      for rev in val['revisions']:
          try:
             # In the case that some revisions are hidden in the API, the
             # collection process skips the revision.
             yield rename(rev, page_id)
             cnt += 1
          except:
             pass
  while ('continue' in data and 'rvcontinue' in data['continue']):
      logging.info("PROGRESS LOG: fetching page %d: %d revisions fetched." % (page_id, cnt))
      atts['rvcontinue'] = data['continue']['rvcontinue']
      while True:
         response = requests.get(baseurl, params = atts)
         if response.status_code != 429:
            break
         time.sleep(10)
      data = response.json()
      for page, val in data['query']['pages'].items():
          for rev in val['revisions']:
              try:
                 yield rename(rev, page_id)
                 cnt += 1
              except:
                 pass

if __name__ == '__main__':
  logging.getLogger().setLevel(logging.INFO)
  parser = argparse.ArgumentParser()
  parser.add_argument('-p', '--page_ids', dest='page_ids',\
                      nargs='+', default=default_page_ids, type=int)
  page_ids = parser.parse_args().page_ids
  for page_id in page_ids:
      with open("testdata/page_%d.json" % page_id, 'w') as f:
           for r in get_revision(page_id):
               f.write(json.dumps(r) + '\n')
      logging.info("PROGRESS LOG: page %d data fetched." % (page_id))
