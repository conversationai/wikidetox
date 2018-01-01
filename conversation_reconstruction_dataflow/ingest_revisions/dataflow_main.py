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

Dataflow Main

A dataflow pipeline to ingest the Wikipedia dump from 7zipped xml files to json.

Run with:

python dataflow_main.py --setup_file ./setup.py 

"""

from __future__ import absolute_import

import argparse
import logging
import subprocess
from threading import Timer
import json
import sys
import zlib
import copy
from os import path
import xml.sax
from ingest_utils import wikipedia_revisions_ingester as wiki_ingester
import math
import os

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import SetupOptions
from apache_beam.io import ReadFromText
from apache_beam.io import WriteToText
from apache_beam.pipeline import AppliedPTransform
from apache_beam.io.gcp import bigquery #WriteToBigQuery

THERESHOLD = 10485760 
my_timeout = 15 * 60 * 60 # 15 hours timeout

def run(known_args, pipeline_args):
  """Main entry point; defines and runs the ingestion pipeline."""

  pipeline_args.extend([
    '--runner=DataflowRunner',
    '--project=wikidetox-viz',
    '--staging_location=gs://wikidetox-viz-dataflow/staging',
    '--temp_location=gs://wikidetox-viz-dataflow/tmp',
    '--job_name=yiqing-ingest-job-truncated-content-run-in-batch',
    '--num_workers=90',
  ])

  pipeline_options = PipelineOptions(pipeline_args)
  pipeline_options.view_as(SetupOptions).save_main_session = True
  if not(known_args.batchno == None):
     known_args.input = 'gs://wikidetox-viz-dataflow/input_lists/7z_file_list_batched_%d'%(known_args.batchno)
     known_args.table = 'wikidetox-viz:wikidetox_conversations.ingested_conversations_batch_%d'%(known_args.batchno)   
     print('Running batch %d'%(known_args.batchno))    
  with beam.Pipeline(options=pipeline_options) as p:
    pcoll = (p | ReadFromText(known_args.input)
                   | beam.ParDo(WriteDecompressedFile())
                   | beam.io.Write(bigquery.BigQuerySink(known_args.table, schema=known_args.schema, validate = True)))

def truncate_content(s):
    """
      Truncate a large revision into small pieces. BigQuery supports line size less than 10MB. 
      Input: Ingested revision in json format, 
              - Fields with data type string: sha1,user_id,format,user_text,timestamp,text,page_title,model,page_namespace,page_id,rev_id,comment, user_ip
      Output: A list of ingested revisions as dictionaries, each dictionary has size <= 10MB.
              - Contains same fields with input 
              - Constains additional fields: truncated:BOOLEAN,records_count:INTEGER,record_index:INTEGER
              - The list if revisions shared the same basic information expect 'text'
              - Concatenating the 'text' field of the list returns the original text content.
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


class WriteDecompressedFile(beam.DoFn):
  def process(self, element):
    logging.info('USERLOG: Working on %s' % element)
    chunk_name = element

    in_file_path = path.join('gs://wikidetox-viz-dataflow/raw-downloads/', chunk_name)

    logging.info('USERLOG: Running gsutil %s ./' % in_file_path)
    cp_local_cmd = (['gsutil', 'cp', in_file_path, './'])
    subprocess.call(cp_local_cmd)

    logging.info('USERLOG: Running ingestion process on %s' % chunk_name)
    ingestion_cmd = ['python2', '-m', 'ingest_utils.run_ingester', '-i', chunk_name]
    status = 'success'
    kill = lambda process, status: process.kill();status='timeout'
    ingest_proc = subprocess.Popen(ingestion_cmd, stdout=subprocess.PIPE, bufsize = 4096)
    timer = Timer(my_timeout, kill, (ingest_proc, status))
    timer.start()
    ingest_proc.wait()
    timer.cancel()
    cnt = 0
    maxsize = 0
    for i, line in enumerate(ingest_proc.stdout):
      try:
         content = json.loads(line) 
      except:
         break
      last_revision = content['rev_id']
      ret = truncate_content(line)
      for r in ret:
          yield r
      if len(ret) > 1:
         logging.info('USERLOG: File %s contains large row, rowsize %d, being truncated to %d pieces' % (chunk_name, sys.getsizeof(line), len(ret)))
      maxsize = max(maxsize, sys.getsizeof(line))
      cnt += 1
    logging.info('USERLOG: Ingestion on file %s complete! %s lines emitted, maxsize: %d, last_revision %s, finishing status: %s' % (chunk_name, cnt, maxsize, last_revision, status))

if __name__ == '__main__':
  logging.getLogger().setLevel(logging.INFO)
  parser = argparse.ArgumentParser()
  parser.add_argument('--batchno', 
                      dest='batchno',
                      default=None,
                      type=int, 
                      help='If you want to run the input dumps in batch, pick a batch number to run')
  parser.add_argument('--input',
                      dest='input',
                      default='gs://wikidetox-viz-dataflow/input_lists/7z_file_list_stuck',
                      help='Input file to process.')
  # Destination BigQuery Table
  schema = 'sha1:STRING,user_id:STRING,format:STRING,user_text:STRING,timestamp:STRING,text:STRING,page_title:STRING,model:STRING,page_namespace:STRING,page_id:STRING,rev_id:STRING,comment:STRING, user_ip:STRING, truncated:BOOLEAN,records_count:INTEGER,record_index:INTEGER'
  parser.add_argument('--table',
                      dest='table',
                      default='wikidetox-viz:wikidetox_conversations.ingested_conversations_stuck',
                      help='Output table to write results to.')
  parser.add_argument('--schema',
                      dest='schema',
                      default=schema,
                      help='Output table schema.')

  known_args, pipeline_args = parser.parse_known_args()
  run(known_args, pipeline_args)

