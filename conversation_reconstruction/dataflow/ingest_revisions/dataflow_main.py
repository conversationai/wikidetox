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

Args:

output: the data storage where you want to store the ingested results
language: the language of the wikipedia data you want to extract, e.g. en, fr, zh
dumpdate: the dumpdate of the wikipedia data, e.g. latest
"""

from __future__ import absolute_import

import logging
import subprocess
from threading import Timer
import json
import sys
import zlib
import copy
from os import path
from ingest_utils.wikipedia_revisions_ingester import parse_stream 
import math
import os
import time
import urllib2
import urllib

from HTMLParser import HTMLParser
import re
import argparse

import apache_beam as beam
from apache_beam.metrics.metric import Metrics
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import SetupOptions
from apache_beam.io import ReadFromText
from apache_beam.io import WriteToText
from apache_beam.io import filesystems
from datetime import datetime


def run(known_args, pipeline_args, sections):
  """Main entry point; defines and runs the ingestion pipeline."""

  pipeline_args.extend([
    '--runner=DataflowRunner',
    '--project=wikidetox-viz',
    '--staging_location=gs://wikidetox-viz-dataflow/staging',
    '--temp_location=gs://wikidetox-viz-dataflow/tmp',
    '--job_name=ingest-latest-revisions',
    '--num_workers=30',
  ])

  pipeline_options = PipelineOptions(pipeline_args)
  pipeline_options.view_as(SetupOptions).save_main_session = True
  with beam.Pipeline(options=pipeline_options) as p:
    pcoll = (p | "GetDataDumpList" >> beam.Create(sections)
            | "Ingestion" >> beam.ParDo(WriteDecompressedFile(), known_args.dumpdate, known_args.language)
            | "AddGroupByKey" >> beam.Map(lambda x: ('{week}at{year}'.format(week=x['week'], year=x['year']), x))
            | "Window" >> beam.WindowInto(beam.window.FixedWindows(10))
            | "ShardByWeek" >>beam.GroupByKey()
            | "WriteToStorage" >> beam.ParDo(WriteToStorage(), known_args.output, known_args.dumpdate, known_args.language))

class WriteDecompressedFile(beam.DoFn):
  def __init__(self):
      self.processed_revisions = Metrics.counter(self.__class__, 'processed_revisions')

  def process(self, element, dumpdate = None, language = None):
    """Downloads a data dump file, store in cloud storage.
       Ingests the xml dump into json, returns the josn records
    """
    mirror, chunk_name =  element

    logging.info('USERLOG: Download data dump %s to cloud storage.' % chunk_name)
    # Download and upload the raw data dump
    dump_path = path.join('gs://wikidetox-viz-dataflow/raw-downloads/%s-%s/'%(language, dumpdate), chunk_name)
    url = mirror + "/" + chunk_name
    if not(os.path.exists(chunk_name)): # For local testing efficiency
       if filesystems.FileSystems.exists(dump_path):
          os.system("gsutil cp %s %s"%(dump_path, chunk_name))
       else:
          urllib.urlretrieve(url, chunk_name)
          os.system("gsutil cp %s %s"%(chunk_name, dump_path))
    # Decompress the data dump
    logging.info('USERLOG: Running ingestion process on %s' % chunk_name)
    input_file = chunk_name[:-3]
    if not(os.path.exists(input_file)): # For local testing
       os.system("7z x %s"%chunk_name)
    # Running ingestion on the xml file
    last_revision = 'None'
    last_completed = time.time()
    for i, content in enumerate(parse_stream(input_file)):
      self.processed_revisions.inc()
      # Add the week and year field for sharding
      dt = datetime.strptime(content['timestamp'], "%Y-%m-%dT%H:%M:%SZ")
      year, week = dt.isocalendar()[:2]
      content['year'] = year
      content['week'] = week
      last_revision = content['rev_id']
      yield content
      logging.info('CHUNK {chunk}: revision {revid} ingested, time elapsed: {time}.'.format(chunk=chunk_name, revid=last_revision, time=time.time() - last_completed))
      last_completed = time.time()
    logging.info('USERLOG: Ingestion on file %s complete! %s lines emitted, last_revision %s' % (chunk_name, i, last_revision))

class WriteToStorage(beam.DoFn):
  def process(self, element, outputdir, dumpdate, language):
      (key, val) = element
      week, year = [int(x) for x in key.split('at')]
      cnt = 0
      # Creates writing path given the week, year pair
      date_path = "{outputdir}/{date}-{lan}/date-{week}at{year}/".format(outputdir=outputdir, date=dumpdate, lan=language, week=week, year=year)
      file_path = 'revisions-{cnt:06d}.json'
      write_path = path.join(date_path, file_path.format(cnt=cnt))
      while filesystems.FileSystems.exists(write_path):
         cnt += 1
         write_path = path.join(date_path, file_path.format(cnt=cnt))
      # Writes to storage
      logging.info('USERLOG: Write to path %s.'%write_path)
      outputfile = filesystems.FileSystems.create(write_path)
      for output in val:
          outputfile.write(json.dumps(output) + '\n')
      outputfile.close()

class ParseDirectory(HTMLParser):
  def __init__(self):
    self.files = []
    HTMLParser.__init__(self)

  def handle_starttag(self, tag, attrs):
    self.files.extend(attr[1] for attr in attrs if attr[0] == 'href')

  def files(self):
    return self.files

def directory(mirror):
  """Download the directory of files from the webpage.
  This is likely brittle based on the format of the particular mirror site.
  """
  # Download the directory of files from the webpage for a particular language.
  parser = ParseDirectory()
  directory = urllib2.urlopen(mirror)
  parser.feed(directory.read().decode('utf-8'))
  # Extract the filenames of each XML meta history file.
  meta = re.compile('^[a-zA-Z-]+wiki-latest-pages-meta-history.*\.7z$')
  return [(mirror, filename) for filename in parser.files if meta.match(filename)]

if __name__ == '__main__':
  logging.getLogger().setLevel(logging.INFO)
  parser = argparse.ArgumentParser()
  parser.add_argument('--output',
                      dest='output',
                      default='gs://wikidetox-viz-dataflow/ingested',
                      help='Specify the output storage in cloud.')
  parser.add_argument('--language',
                      dest='language',
                      default='en',
                      help='Specify the language of the Wiki Talk Page you want to ingest.')
  parser.add_argument('--dumpdate',
                      dest='dumpdate',
                      default='latest',
                      help='Specify the date of the Wikipedia data dump.')
  known_args, pipeline_args = parser.parse_known_args()
  dumpstatus_url = 'https://dumps.wikimedia.org/{lan}wiki/{date}/dumpstatus.json'.format(lan=known_args.language, date=known_args.dumpdate)
  try:
     response = urllib2.urlopen(dumpstatus_url)
     dumpstatus = json.loads(response.read())
  except:
     dumpstatus = None
  if not(dumpstatus):
     mirror = 'http://dumps.wikimedia.your.org/{lan}wiki/latest'.format(lan=known_args.language)
     sections = directory(mirror)
  else:
     url = 'https://dumps.wikimedia.org/{lan}wiki/{date}'.format(lan=known_args.language, date=known_args.dumpdate)
     sections = [(url, filename) for filename in dumpstatus['jobs']['metahistory7zdump']['files'].keys()]
  run(known_args, pipeline_args, sections)
