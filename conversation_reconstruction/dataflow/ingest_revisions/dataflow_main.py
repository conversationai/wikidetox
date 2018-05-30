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

import logging
import subprocess
from threading import Timer
import json
import sys
import zlib
import copy
from os import path
from ingest_utils import wikipedia_revisions_ingester as wiki_ingester
import math
import os
import time
import urllib2
import urllib

from HTMLParser import HTMLParser
import re
import shutil
import argparse

import apache_beam as beam
from apache_beam.metrics.metric import Metrics
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import SetupOptions
from apache_beam.io import ReadFromText
from apache_beam.io import WriteToText
from apache_beam.io import filesystems
from apache_beam.pipeline import AppliedPTransform
from apache_beam.io.gcp import bigquery #WriteToBigQuery
from datetime import datetime


class ParseDirectory(HTMLParser):
  def __init__(self):
    self.files = []
    HTMLParser.__init__(self)

  def handle_starttag(self, tag, attrs):
    self.files.extend(attr[1] for attr in attrs if attr[0] == 'href')

  def files(self):
    return self.files

def run(sections):
  """Main entry point; defines and runs the ingestion pipeline."""

  pipeline_args = [
    '--runner=DirectRunner',
    '--project=wikidetox-viz',
    '--staging_location=gs://wikidetox-viz-dataflow/staging',
    '--temp_location=gs://wikidetox-viz-dataflow/tmp',
    '--job_name=ingest-latest-revisions',
    '--num_workers=30',
  ]

  pipeline_options = PipelineOptions(pipeline_args)
  pipeline_options.view_as(SetupOptions).save_main_session = True
  sections = sections[:1]
  with beam.Pipeline(options=pipeline_options) as p:
    pcoll = (p | beam.Create(sections)
            | beam.ParDo(WriteDecompressedFile())
            | beam.Map(lambda x: ('{week}at{year}'.format(week=x['week'], year=x['year']), x))
            | beam.GroupByKey()
            | beam.ParDo(WriteToStorage()))

class WriteToStorage(beam.DoFn):
  def process(self, element):
      (key, val) = element
      week, year = [int(x) for x in key.split('at')]
      write_path = path.join('gs://wikidetox-viz-dataflow/ingested-%s-%s/'%(known_args.dumpdate, known_args.language), 'date-{week}at{year}/revisions.json'.format(week=week, year=year))
      logging.info('USERLOG: Write to path %s.'%path)
      outputfile = filesystems.FileSystems.create(write_path)
      for output in val:
          outputfile.write(json.dumps(output) + '\n')
      outputfile.close()

def directory(mirror):
  """Download the directory of files from the webpage.

  This is likely brittle based on the format of the particular mirror site.

  Args:
    mirror: the base url (with language) of the wiki to scan.

  Returns:
    A list of filenames for compressed meta-history files for that langauge.
  """
  # Download the directory of files from the webpage for a particular language.
  parser = ParseDirectory()
  directory = urllib2.urlopen(mirror)
  parser.feed(directory.read().decode('utf-8'))
  # Extract the filenames of each XML meta history file.
  meta = re.compile('^[a-zA-Z-]+wiki-latest-pages-meta-history.*\.7z$')
  return [json.dumps((mirror, filename)) for filename in parser.files if meta.match(filename)]

def add_week_year_fields(dic):
    dt = datetime.strptime(dic['timestamp'], "%Y-%m-%dT%H:%M:%SZ")
    year, week = dt.isocalendar()[:2]
    dic['year'] = year
    dic['week'] = week
    return dic

class WriteDecompressedFile(beam.DoFn):
  def __init__(self):
      self.processed_revisions = Metrics.counter(self.__class__, 'processed_revisions')

  def process(self, element):
    mirror, chunk_name = json.loads(element)

    logging.info('USERLOG: Download data dump %s to cloud storage.' % chunk_name)
    url = mirror + "/" + chunk_name
    urllib.urlretrieve(url, chunk_name)
    dump_path = path.join('gs://wikidetox-viz-dataflow/raw-downloads-%s-%s/'%(known_args.dumpdate, known_args.language), chunk_name)
    os.system("gsutil cp %s %s"%(chunk_name, dump_path))

    logging.info('USERLOG: Running ingestion process on %s' % chunk_name)
    os.system("7z x %s"%chunk_name)
    input_file = chunk_name[:-3]
    last_revision = 'None'
    last_completed = time.time()
    for i, content in enumerate(wiki_ingester.parse_stream(input_file)):
      self.processed_revisions.inc()
      ret = add_week_year_fields(content)
      last_revision = content['rev_id']
      yield ret
      logging.info('CHUNK {chunk}: revision {revid} ingested, time elapsed: {time}.'.format(chunk=chunk_name, revid=last_revision, time=time.time() - last_completed))
      last_completed = time.time()
    logging.info('USERLOG: Ingestion on file %s complete! %s lines emitted, last_revision %s' % (chunk_name, i, last_revision))

if __name__ == '__main__':
  logging.getLogger().setLevel(logging.INFO)
  parser = argparse.ArgumentParser()
  parser.add_argument('--output',
                      dest='output',
                      default='gs://wikidetox-viz-dataflow/ingested/',
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
  mirror = 'http://dumps.wikimedia.your.org/{lan}wiki/{date}'.format(lan=known_args.language, date=known_args.dumpdate)
  sections = directory(mirror)
  run(sections)
