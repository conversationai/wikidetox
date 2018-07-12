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

Dataflow Main

A dataflow pipeline to ingest the Wikipedia dump from 7zipped xml files to json.

To configure with boto:

  Run gsutil config -e

Run with:

python dataflow_main.py --setup_file ./setup.py

Args:

ingestFrom: choose from the three options : {wikipedia, local, cloud}:
  - wikipedia: performs the downloading job from Wikipedia, run with:
               [python dataflow_main.py --setup_file ./setup.py
               --ingestFrom=wikipedia --download --language=YourLanguage
               --dumpdate=YourDumpdate --cloudBucket=YourCloudBucket]
  - local: Tests the pipeline locally, run the code with
           [python dataflow_main.py --setup_file ./setup.py
            --ingestFrom=local --localStorage=YourLocalStorage --testmode]
  - cloud: Reads from downloaded bz2 files on cloud, performs the ingestion job,
    run the code with
           [python dataflow_main.py --setup_file ./setup.py
           --ingestFrom=cloud --cloudBucket=YourCloudBucket(without gs:// prefix)
           (Optional) --extract_all_edits
           (Optional) --cloudlist=YourInputListLocation
           (Optional) --cloudlistStartFrom=startProcessingPointInTheList
           (Optional) --cloudlistEnd=endProcessingPointInTheList
           (Optional) --selected_pages=CloudStorageWithListOfSelectedPages]
           (Optional) --ingest

ingest: If turned on, this pipeline will ingest revisions into json formats.
language: the language of the wikipedia data you want to extract, e.g. en, fr, zh
dumpdate: the dumpdate of the wikipedia data, e.g. latest
testmode: if turned on, the pipeline runs on DirectRunner.
localStorage: the location of the local test file.
download: if turned on, the pipeline only performs downloading job from Wikipedia.
cloudBucket: the cloud bucket where the ingestion reads from or the download stores to.
extract_all_edits: If turned on, this pipeline will process all edits as opposed to only edits with POV in comment.
"""

from __future__ import absolute_import

import logging
import subprocess
from threading import Timer
import json
import sys
import zlib
import copy
import bz2
from os import path
from ingest_utils.wikipedia_revisions_ingester import parse_stream
from ingest_utils.process import isSimilar
import os
import time
import urllib
import urllib2
import StringIO
import mwparserfromhell

from HTMLParser import HTMLParser
import re
import argparse
import boto
import gcs_oauth2_boto_plugin
# boto needs to be configured, see here:
# https://cloud.google.com/storage/docs/boto-plugin#setup-python

import apache_beam as beam
from apache_beam.metrics.metric import Metrics
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import SetupOptions
from apache_beam.io import ReadFromText
from apache_beam.io import WriteToText
from apache_beam.io import filesystems
from datetime import datetime
import nltk
import resource
from threading import Timer
import signal


MEMLIMIT = 1024 * 1024 * 1024
my_timeout = 2


GOOGLE_STORAGE = 'gs'
LOCAL_STORAGE = 'file'
CONTEXT_RANGE = 3
LINE_THERESHOLD = 10000
INTERVAL = 20

def run(known_args, pipeline_args, sections, jobname):
  """Main entry point; defines and runs the ingestion pipeline."""

  if known_args.testmode:
    # In testmode, disable cloud storage backup and run on directRunner
    pipeline_args.append('--runner=DirectRunner')
  else:
    pipeline_args.append('--runner=DataflowRunner')

  pipeline_args.extend([
    '--project=wikidetox',
    '--staging_location=gs://wikidetox-dataflow/staging',
    '--temp_location=gs://wikidetox-dataflow/tmp',
    '--job_name=extract-edits-{}'.format(jobname),
    '--num_workers=20',
  ])

  pipeline_options = PipelineOptions(pipeline_args)
  pipeline_options.view_as(SetupOptions).save_main_session = True
  with beam.Pipeline(options=pipeline_options) as p:
    pcoll = (p | "GetDataDumpList" >> beam.Create(sections))
    cloud_storage = ("gs://wikidetox-dataflow/article_edits/{lan}-{date}".
                     format(lan=known_args.language, date=known_args.dumpdate))
    if known_args.download:
       pcoll = (pcoll |
                "DownloadDataDumps" >> beam.ParDo(DownloadDataDumps(), known_args.bucket))
    else:
      if known_args.ingest:
        if known_args.POVpages is not None:
           selected_pages = (p | "GetSelectedPages" >> beam.io.ReadFromText(known_args.POVpages)
                             | beam.Map(lambda x: (eval(x)['chunk_name'], eval(x)['page_id'])))
           pcoll = (pcoll | beam.Map(lambda x: (x, x)))
           pipeline_input = ({"selected_pages": selected_pages, "datadump": pcoll} | beam.CoGroupByKey())
        else:
           pipeline_input = pcoll
        pipeline_input = ( pipeline_input |
            "Ingestion" >> beam.ParDo(IngestDumps(), known_args.bucket,
                                      known_args.ingestFrom, known_args.all_edits) |
                          "WriteIngested" >> beam.io.WriteToText(path.join(cloud_storage, 'ingested-revisions-{}'.format(jobname))))
      else:
        error_log, rejects, improvments, non_rejects, sent_revises = ( p |
            "ReadIngested" >> beam.io.ReadFromText(path.join(cloud_storage, 'ingested-revisions-{}*'.format(jobname))) |
            "GetDiffs" >> beam.ParDo(WriteDecompressedFile()).with_outputs(
                     'rejects', 'improvments', 'non_rejects', 'sent_revises', main = 'error_log'))
        (sent_revises | "SentRevisesToStorage" >>
         beam.io.WriteToText(path.join(cloud_storage, 'sent_revise-{}'.format(jobname))))
        (rejects | "RejectedToStorage" >>
         beam.io.WriteToText(path.join(cloud_storage, 'rejected-{}'.format(jobname))))
        (improvments | "InsertsToStorage" >>
         beam.io.WriteToText(path.join(cloud_storage, 'improved-{}'.format(jobname))))
        (non_rejects | "NonRejectsToStorage" >>
         beam.io.WriteToText(path.join(cloud_storage, 'non_rejected-{}'.format(jobname))))
        (error_log | "ERRORlog" >>
         beam.io.WriteToText(path.join(cloud_storage, 'error_log-{}'.format(jobname))))


class DownloadDataDumps(beam.DoFn):
  def process(self, element, bucket):
    """Downloads a data dump file, store in cloud storage.
       Returns the cloud storage location.
    """
    mirror, chunk_name =  element
    logging.info('USERLOG: Download data dump %s to store in cloud storage.' % chunk_name)
    # Download data dump from Wikipedia and upload to cloud storage.
    url = mirror + "/" + chunk_name
    write_path = path.join('gs://', bucket, chunk_name)
    urllib.urlretrieve(url, chunk_name)
    os.system("gsutil cp %s %s" % (chunk_name, write_path))
    os.system("rm %s" % chunk_name)
    yield chunk_name
    return


class IngestDumps(beam.DoFn):
  def __init__(self):
      self.processed_revisions = Metrics.counter(self.__class__, 'processed_revisions')

  def process(self, element, bucket, ingestFrom, all_edits):
    """Ingests the xml dump into consecutive revision pairs in json format.
    """
    if isinstance(element, basestring):
      chunk_name = element
      page_ids = None
    else:
      # If specified on selected pages.
      (chunk_name, data) = element
      if data['datadump'] == []:
         logging.info('USERLOG: chunk %s skipped.' % chunk_name)
         return
      page_ids = data['selected_pages']
    logging.info('USERLOG: Running ingestion process on %s' % chunk_name)
    if ingestFrom == 'local':
       input_stream = chunk_name
    else:
       cmd = "gsutil -m cp %s %s" % (path.join('gs://', bucket, chunk_name), chunk_name)
       status = os.WEXITSTATUS(os.system(cmd))
       if status  != 0:
         raise Exception("GSUTIL COPY Error, exited with status %d" % status)
       input_stream = chunk_name
    # Running ingestion on the xml file
    last_revision = None
    last_completed = time.time()
    i = 0
    for i, content in enumerate(parse_stream(bz2.BZ2File(chunk_name))):
      if (page_ids is not None) and (content['page_id'] not in page_ids):
        continue
      self.processed_revisions.inc()
      if content['text'] is None:
        content['text'] = ""
      if (content["comment"] is not None and "POV" in content["comment"]) or all_edits:
        yield json.dumps((last_revision, content))
      logging.info('INGESTION_LOG: CHUNK {chunk}: revision {revid} ingested, time elapsed: {time}.'.format(
          chunk=chunk_name, revid=content['rev_id'], time=time.time() - last_completed))
      last_completed = time.time()
    if ingestFrom != 'local': os.system("rm %s" % chunk_name)
    logging.info('USERLOG: Ingestion on file %s complete! %s lines emitted' % (chunk_name, i))


class WriteDecompressedFile(beam.DoFn):
  def __init__(self):
      self.processed_revision_pairs = Metrics.counter(self.__class__, 'processed_revision_pairs')
      self.errors = Metrics.counter(self.__class__, 'errors')
      self.revision_skipped = Metrics.counter(self.__class__, 'processed_revision_pairs')
      self.sentence_revises = Metrics.counter(self.__class__, 'sentence_revises')

  @staticmethod
  def set_memory_limit(soft, hard):
    resource.setrlimit(resource.RLIMIT_AS, (soft, hard))

  def start_bundle(self):
    nltk.download('punkt')

  def process(self, element):
    """Compares two revisions and return the edits.
    """
    (former, content) = json.loads(element)
    if isSimilar(former, content):
      # Only focus on revision pairs that are similar to look for sentence
      # revises.
      logging.info('EDIT_PROCESS_LOG: revision {revid} started.'.format(revid=content['rev_id']))
      self.processed_revision_pairs.inc()
      # Add memory and time limit to edit processing to prevent pipeline
      # crashes.

      tf = tempfile.NamedTemporaryFile(delete=False)
      json.dump((former, content), tf)
      tf.close()
      process_cmd = ['python2', '-m', 'ingest_utils.run_processor', '-i', tf.name]
      try:
        sub_proc = subprocess.Popen(process_cmd, stdout=subprocess.PIPE, preexec_fn=WriteDecompressedFile.set_memory_limit(MEMLIMIT, -1))
      except MemoryError:
        # If errors encountered.
        yield beam.pvalue.TaggedOutput('error_log', json.dumps({"revision": content['rev_id'], "page_id": content["page_id"]}))
        self.errors.inc()
      else:
        timer = Timer(my_timeout, sub_proc.kill())
        timer.start()
        ret, stderr = sub_proc.communicate()
        sub_proc.wait()
        timer.cancel()
        WriteDecompressedFile.set_memory_limit(-1, -1)

        if ret == "" or ret == None:
          # If errors encountered.
          yield beam.pvalue.TaggedOutput('error_log', json.dumps({"revision": content['rev_id'], "page_id": content["page_id"]}))
          self.errors.inc()
        else:
          # If the parsing finishes.
          (context_equals, inserts, deletes, sentence_revises) = ret
          metadata = {f : content[f] for f in ['comment', 'user_id', 'user_text',
                                              'user_ip', 'page_id', 'page_title']}
          ret = {"rejecter" : content['rev_id']}
          ret.update(metadata)
          for d in deletes:
            ret['content'] = d
            yield beam.pvalue.TaggedOutput('rejects', json.dumps(ret))
          for sent in inserts:
            ret['content'] = sent
            yield beam.pvalue.TaggedOutput('improvments', json.dumps(ret))
          for sent in context_equals:
            ret['content'] = sent
            yield beam.pvalue.TaggedOutput('non_rejects', json.dumps(ret))
          del ret['content']
          for i, (sent1, sent2) in enumerate(sentence_revises):
            ret['original_content'] = sent1
            ret['revised_content'] = sent2
            yield beam.pvalue.TaggedOutput('sent_revises', json.dumps(ret))
          self.sentence_revises.inc(i)
          logging.info('INGESTION_LOG: revision {revid} processed.'.format(revid=content['rev_id']))
    else:
      self.revision_skipped.inc()

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
  meta = re.compile('^[a-zA-Z-]+wiki-latest-pages-meta-history.*\.bz2$')
  return [(mirror, filename) for filename in parser.files if meta.match(filename)]

if __name__ == '__main__':
  logging.getLogger().setLevel(logging.INFO)
  # Define parameters
  parser = argparse.ArgumentParser()
  # Options: local, cloud
  parser.add_argument('--ingestFrom',
                      dest='ingestFrom',
                      default='none')
  parser.add_argument('--download',
                      dest='download',
                      action='store_true')
  parser.add_argument('--cloudBucket',
                      dest='bucket',
                      default='wikidetox-dataflow/raw-downloads/en-20180601/',
                      help='Specify the cloud storage location to store/stores the raw downloads.')
  parser.add_argument('--language',
                      dest='language',
                      default='en',
                      help='Specify the language of the Wiki Talk Page you want to ingest.')
  parser.add_argument('--dumpdate',
                      dest='dumpdate',
                      default='20180501',
                      help='Specify the date of the Wikipedia data dump.')
  parser.add_argument('--localStorage',
                      dest='localStorage',
                      default='ingest_utils/testdata/test_wiki_dump.xml.bz2',
                      help='If ingest from local storage, please specify the location of the input file.')
  parser.add_argument('--testmode',
                      dest='testmode',
                      action='store_true')
  parser.add_argument('--cloudlist',
                      dest='cloudlist',
                      default=None,
                      help='Provide a list of dumps (separated by line break) in a local file you want to process from the cloudbucket.')
  parser.add_argument('--cloudlistStartFrom',
                      type=int,
                      dest='start',
                      default=None,
                      help='(Optional) start processing from any point in the cloudlist.')
  parser.add_argument('--cloudlistEnd',
                      type=int,
                      dest='end',
                      default=None,
                      help='(Optional) end processing from any point in the cloudlist.')
  parser.add_argument('--selected_pages',
                      dest='POVpages',
                      default=None,
                      help='(Optional) List of selected pages to be processed on')
  parser.add_argument('--extract_all_edits',
                      dest='all_edits',
                      action='store_true',
                      help='If turned on, this pipeline will process all edits as opposed to only edits with POV in comment.')
  parser.add_argument('--ingest',
                      dest='ingest',
                      action='store_true',
                      help='If turned on, this pipeline will ingest revisions into json formats.')


  known_args, pipeline_args = parser.parse_known_args()
  if known_args.download:
     # If specified downloading from Wikipedia
     dumpstatus_url = 'https://dumps.wikimedia.org/{lan}wiki/{date}/dumpstatus.json'.format(lan=known_args.language, date=known_args.dumpdate)
     response = urllib2.urlopen(dumpstatus_url)
     try:
        response = urllib2.urlopen(dumpstatus_url)
        dumpstatus = json.loads(response.read())
        url = 'https://dumps.wikimedia.org/{lan}wiki/{date}'.format(lan=known_args.language, date=known_args.dumpdate)
        sections = [(url, filename) for filename in dumpstatus['jobs']['metahistorybz2dump']['files'].keys()]
     except:
        # In the case dumpdate is not specified or is invalid, download the
        # latest version.
        mirror = 'http://dumps.wikimedia.your.org/{lan}wiki/latest'.format(lan=known_args.language)
        sections = directory(mirror)
  if known_args.ingestFrom == "cloud":
     if known_args.cloudlist is not None:
       sections = []
       with open(known_args.cloudlist) as f:
         for line in f:
             sections.append(line[:-1])
     else:
        sections = []
        uri = boto.storage_uri(known_args.bucket, GOOGLE_STORAGE)
        prefix = known_args.bucket[known_args.bucket.find('/')+1:]
        for obj in uri.list_bucket(prefix=prefix):
           sections.append(obj.name[obj.name.rfind('/') + 1:])
  if known_args.ingestFrom == 'local':
     sections = [known_args.localStorage]
  if known_args.start is not None:
     start = known_args.start
  else:
     start = 0
  if known_args.end is not None:
     end = known_args.end
  else:
     end = len(sections)
  run(known_args, pipeline_args,
      sections[start:end],
      "{fr}-{to}".format(fr=start, to=end))
