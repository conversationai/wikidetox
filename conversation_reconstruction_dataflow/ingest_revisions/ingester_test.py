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

Ingester Test

A unit test for wikipedia_revisions_ingester.py and run_ingester.py

Run with  python -m ingest_utils.ingester_test
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import unittest
import json
import xml.sax
import subprocess
import os
import signal
import sys
import copy

from threading import Timer
from os import path
from ingest_utils import wikipedia_revisions_ingester as wiki_ingester
import math
THERESHOLD = 500

def truncate_content(s):
    """
      Truncate a large revision into small pieces. BigQuery supports line size less than 10MB. 
      Input: Ingested revision in json format, 
              - Fields with data type string: sha1,user_id,format,user_text,timestamp,text,page_title,model,page_namespace,page_id,rev_id,comment, user_ip
      Output: A list of ingested revisions as dictionaries, each dictionary has size <= 10MB.
              - Contains same fields with input 
              - Constains additional fields: truncated:BOOLEAN,records_count:INTEGER,record_index:INTEGER
              - The list if revisions shared the same basic information expect 'comment'
              - Concatenating the 'comment' field of the list returns the original comment content.
    """
    dic = json.loads(s) 
    dic['truncated'] = False
    dic['records_count'] = 1
    dic['record_index'] = 0
    filesize = sys.getsizeof(s)
    if filesize <= THERESHOLD:
       return [dic]
    else:
       l = len(dic['text'])
       contentsize = sys.getsizeof(dic['text'])
       pieces = math.ceil(contentsize / (THERESHOLD - (filesize - contentsize)))
       piece_size = int(l / pieces)
       dic['truncated'] = True
       dics = []
       last = 0
       ind = 0
       while (last < l):
           cur_dic = copy.deepcopy(dic)
           if last + piece_size >= l:
              cur_dic['text'] = cur_dic['text'][last:]
           else:
              cur_dic['text'] = cur_dic['text'][last:last+piece_size]
           last += piece_size
           cur_dic['record_index'] = ind
           dics.append(cur_dic)
           ind += 1
       no_records = len(dics)
       for dic in dics:
           dic['records_count'] = no_records
       return dics



class TestWikiIngester(unittest.TestCase):
  def test_ingester(self):
    input_file = path.join('ingest_utils', 'testdata', 'test_wiki_dump.xml')

    kill = lambda process, status: process.kill(); status = 'timeout'
    status = 'success'
    my_timeout = 1
    ingestion_cmd = ['python2', '-m', 'ingest_utils.run_ingester', '-i', input_file]
    ingest_proc = subprocess.Popen(ingestion_cmd, stdout=subprocess.PIPE, bufsize = 4096)
    timer = Timer(my_timeout, kill, (ingest_proc, status))
    timer.start()
    for i, line in enumerate(ingest_proc.stdout):
        print(i)
    ingest_proc.wait()
    timer.cancel()

#      tmp_line = sorted(truncate_content(line), key=lambda d: d['record_index'])
#      concated_content = ''
#      parsed_line = copy.deepcopy(tmp_line[0]) 
#      for cur_line in tmp_line:
#          concated_content += cur_line['text']
#      parsed_line['text'] = concated_content 
#      if i == 0:
#        self.assertEqual(parsed_line['comment'], 'a test comment 1')
#      if i == 1:
#        self.assertEqual(parsed_line['page_title'], 'Third Page (namespace 1)')
#        self.assertEqual(parsed_line['text'], ' The first revision on the third page. Written by Tinker JJ. Has a comment.')
#      if i == 2 or i == 3:
#        self.assertEqual(parsed_line['page_id'], '54197571')
#    self.assertEqual(i, 3)
#    self.assertEqual(status, 'success')

if __name__ == '__main__':
  unittest.main()
