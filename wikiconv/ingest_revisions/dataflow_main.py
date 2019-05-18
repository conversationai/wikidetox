r"""Dataflow Main.

Copyright 2017 Google Inc. Licensed under the Apache License, Version 2.0
(the "License"); you may not use this file except in compliance with the
License.

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
ingestFrom: choose from the three options : {wikipedia, local, cloud}:
  - wikipedia: performs the downloading job from Wikipedia, run with: [
    python dataflow_main.py --setup_file ./setup.py --ingestFrom=wikipedia \
        --download --language=YourLanguage --dumpdate=YourDumpdate \
        --blobPrefix=YourCloudBucket --project=YourGoogleCloudProject \
        --bucket=TemporaryFileBucket
  ]
  - local: Tests the pipeline locally, run the code with [
    python dataflow_main.py --setup_file ./setup.py --ingestFrom=local \
    --localStorage=YourLocalStorage --testmode --output=YourOutputStorage \
    --project=YourGoogleCloudProject --bucket=TemporaryFileBucket
  ]
  - cloud: Reads from downloaded bz2 files on cloud, performs the ingestion job,
    run the code with [
    python dataflow_main.py --setup_file ./setup.py --ingestFrom=cloud \
        --output=gs://bucket/YourOutputStorage --blobPrefix=YourCloudBucket \
        --project=YourGoogleCloudProject --bucket=TemporaryFileBucket
  ]
output: the data storage where you want to store the ingested results
language: the language of the wikipedia data you want to extract, e.g. en, fr,
  zh
dumpdate: the dumpdate of the wikipedia data, e.g. latest
testmode: if turned on, the pipeline runs on DirectRunner.
localStorage: the location of the local test file.
download: if turned on, the pipeline only performs downloading job from
  Wikipedia.
bucket: the cloud storage bucket (gs://thispartonly/not/this).
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import bz2
import datetime
import HTMLParser
import json
import logging
import os
import re
import sys
import time
import urllib
import urllib2

import apache_beam as beam
from ingest_revisions.ingest_utils import wikipedia_revisions_ingester
from google.cloud import storage

LOCAL_STORAGE = 'file'
MEMORY_THERESHOLD = 1000000


def run(known_args, pipeline_args, sections, prefix):
  """Main entry point; defines and runs the ingestion pipeline."""

  if known_args.testmode:
    # In testmode, disable cloud storage backup and run on directRunner
    pipeline_args.append('--runner=DirectRunner')
  else:
    pipeline_args.append('--runner=DataflowRunner')

  pipeline_args.extend([
      '--project={project}'.format(project=known_args.project),
      '--staging_location=gs://{bucket}/staging'.format(
          bucket=known_args.bucket),
      '--temp_location=gs://{bucket}/tmp'.format(bucket=known_args.bucket),
      '--job_name=ingest-latest-revisions-{lan}'.format(
          lan=known_args.language),
      '--num_workers=80',
  ])

  pipeline_options = beam.options.pipeline_options.PipelineOptions(
      pipeline_args)
  pipeline_options.view_as(
      beam.options.pipeline_options.SetupOptions).save_main_session = True
  with beam.Pipeline(options=pipeline_options) as p:
    pcoll = (p | 'GetDataDumpList' >> beam.Create(sections))
    if known_args.download:
      pcoll = (
          pcoll | 'DownloadDataDumps' >> beam.ParDo(DownloadDataDumps(),
                                                    known_args.bucket, prefix))
    else:
      pcoll = (
          pcoll |
          'Ingestion' >> beam.ParDo(WriteDecompressedFile(), known_args.bucket,
                                    prefix, known_args.ingest_from)
          | 'AddGroupByKey' >> beam.Map(lambda x: (x['year'], x))
          | 'ShardByYear' >> beam.GroupByKey()
          | 'WriteToStorage' >> beam.ParDo(WriteToStorage(), known_args.output,
                                           known_args.dumpdate,
                                           known_args.language))


class DownloadDataDumps(beam.DoFn):
  """Download the bulk wikipedia xml dumps from mirrors."""

  def start_bundle(self):
    self._storage_client = storage.Client()

  def process(self, element, bucket, blob_prefix):
    """Downloads a data dump file, store in cloud storage.

    Args:
      element: beam input record.
      bucket: a cloud storage bucket name.
      blob_prefix: the path to the filename directory in the bucket.

    Yields:
      the cloud storage location.
    """
    mirror, chunk_name = element
    logging.info('USERLOG: Download data dump %s to store in cloud storage.',
                 chunk_name)
    # Download data dump from Wikipedia and upload to cloud storage.
    urllib.urlretrieve(mirror + '/' + chunk_name, chunk_name)
    self._storage_client.get_bucket(bucket).blob(
        os.path.join(blob_prefix, chunk_name)).upload_from_filename(chunk_name)
    os.remove(chunk_name)
    yield chunk_name
    return


class WriteDecompressedFile(beam.DoFn):
  """Decompress wikipedia file and creates json records."""

  def start_bundle(self):
    self._storage_client = storage.Client()

  def __init__(self):
    self.processed_revisions = beam.metrics.Metrics.counter(
        self.__class__, 'processed_revisions')
    self.large_page_revision_count = beam.metrics.Metrics.counter(
        self.__class__, 'large_page_revision_cnt')

  def process(self, element, bucket, blob_prefix, ingest_from):
    """Ingests the xml dump into json, returns the json records."""
    # Decompress the data dump
    chunk_name = element
    logging.info('USERLOG: Running ingestion process on %s', chunk_name)
    if ingest_from != 'local':
      self._storage_client.get_bucket(bucket).blob(
          os.path.join(blob_prefix,
                       chunk_name)).download_to_filename(chunk_name)
    # Running ingestion on the xml file
    last_revision = 'None'
    last_completed = time.time()
    cur_page_id = None
    page_size = 0
    cur_page_revision_cnt = 0
    i = 0
    for i, content in enumerate(wikipedia_revisions_ingester.parse_stream(
        bz2.BZ2File(chunk_name))):
      self.processed_revisions.inc()
      # Add the year field for sharding
      dt = datetime.datetime.strptime(content['timestamp'],
                                      '%Y-%m-%dT%H:%M:%SZ')
      content['year'] = dt.isocalendar()[0]
      last_revision = content['rev_id']
      yield content
      logging.info(
          'CHUNK %s: revision %s ingested, time elapsed: %g.',
          chunk_name, last_revision, time.time() - last_completed)
      last_completed = time.time()
      if content['page_id'] == cur_page_id:
        page_size += len(json.dumps(content))
        cur_page_revision_cnt += 1
      else:
        if page_size >= MEMORY_THERESHOLD:
          self.large_page_revision_count.inc(cur_page_revision_cnt)
        cur_page_id = content['page_id']
        page_size = len(json.dumps(content))
        cur_page_revision_cnt = 1
    if page_size >= MEMORY_THERESHOLD:
      self.large_page_revision_count.inc(cur_page_revision_cnt)

    if ingest_from != 'local':
      os.remove(chunk_name)
    logging.info(
        'USERLOG: Ingestion on file %s complete! %s lines emitted, last_revision %s',
        chunk_name, i, last_revision)


class WriteToStorage(beam.DoFn):
  """Copys files to gloud storage."""

  def process(self, element, outputdir, dumpdate, language):
    (key, val) = element
    year = int(key)
    cnt = 0
    # Creates writing path given the year pair
    date_path = '{outputdir}/{date}-{lan}/date-{year}/'.format(
        outputdir=outputdir, date=dumpdate, lan=language, year=year)
    file_path = 'revisions-{cnt:06d}.json'
    write_path = os.path.join(date_path, file_path.format(cnt=cnt))
    while beam.io.filesystems.FileSystems.exists(write_path):
      cnt += 1
      write_path = os.path.join(date_path, file_path.format(cnt=cnt))
    # Writes to storage
    logging.info('USERLOG: Write to path %s.', write_path)
    outputfile = beam.io.filesystems.FileSystems.create(write_path)
    for output in val:
      outputfile.write(json.dumps(output) + '\n')
    outputfile.close()


class ParseDirectory(HTMLParser.HTMLParser):
  """Extension of HTMLParser that parses all file in a directory."""

  def __init__(self):
    self.files = []
    HTMLParser.HTMLParser.__init__(self)

  def handle_starttag(self, tag, attrs):
    self.files.extend(attr[1] for attr in attrs if attr[0] == 'href')

  def files(self):
    return self.files


def directory(mirror):
  """Download the directory of files from the webpage.

  This is likely brittle based on the format of the particular mirror site.

  Args:
    mirror: url to load wikipedia data from.

  Returns:
    list of mirror and filename tuples.
  """
  # Download the directory of files from the webpage for a particular language.
  parser = ParseDirectory()
  mirror_directory = urllib2.urlopen(mirror)
  parser.feed(mirror_directory.read().decode('utf-8'))
  # Extract the filenames of each XML meta history file.
  meta = re.compile(r'^[a-zA-Z-]+wiki-latest-pages-meta-history.*\.bz2$')
  return [(mirror, fname) for fname in parser.files if meta.match(fname)]


def get_sections(bucket, blob_prefix):
  """Gets list of basenames from bucket that match a prefix.

  Args:
    bucket: a cloud storage bucket.
    blob_prefix: a path prefix within the storage bucket to scan.

  Returns:
    a list of filename names.
  """
  filenames = []
  for obj in storage.Client().get_bucket(bucket).list_blobs(prefix=blob_prefix):
    filenames.append(obj.name[obj.name.rfind('/') + 1:])
  return filenames


def main(argv=None):
  if argv is None:
    argv = sys.argv
  logging.getLogger().setLevel(logging.INFO)
  # Define parameters
  arg_parser = argparse.ArgumentParser()
  # Options: local, cloud
  arg_parser.add_argument(
      '--project', dest='project', help='Your google cloud project.')
  arg_parser.add_argument(
      '--bucket',
      dest='bucket',
      help='Your google cloud bucket for temporary and staging files.')
  arg_parser.add_argument('--ingestFrom', dest='ingest_from', default='none')
  arg_parser.add_argument('--download', dest='download', action='store_true')
  arg_parser.add_argument(
      '--output', dest='output', help='Specify the output storage in cloud.')
  arg_parser.add_argument(
      '--blobPrefix',
      dest='blob_prefix',
      help='Specify the prefix to assign to blobs for the raw downloads.')
  arg_parser.add_argument(
      '--language',
      dest='language',
      help='Specify the language of the Wiki Talk Page you want to ingest.')
  arg_parser.add_argument(
      '--dumpdate',
      dest='dumpdate',
      help='Specify the date of the Wikipedia data dump.')
  arg_parser.add_argument(
      '--localStorage',
      dest='localStorage',
      help='If ingest from local storage, please specify the location of the input file.'
  )
  arg_parser.add_argument('--testmode', dest='testmode', action='store_true')
  known_args, pipeline_args = arg_parser.parse_known_args()
  if known_args.download:
    # If specified downloading from Wikipedia
    dumpstatus_url = 'https://dumps.wikimedia.org/{lan}wiki/{date}/dumpstatus.json'.format(
        lan=known_args.language, date=known_args.dumpdate)
    response = urllib2.urlopen(dumpstatus_url)
    dumpstatus = json.loads(response.read())
    url = 'https://dumps.wikimedia.org/{lan}wiki/{date}'.format(
        lan=known_args.language, date=known_args.dumpdate)
    if 'files' not in dumpstatus['jobs']['metahistorybz2dump']:
      raise ValueError('Unable to find data for specifid date')
    sections = [(url, filename) for filename in dumpstatus['jobs']
                ['metahistorybz2dump']['files'].keys()]
  prefix = 'raw-downloads/%s-%s' % (known_args.language, known_args.dumpdate)
  if known_args.ingest_from == 'cloud':
    sections = get_sections(known_args.bucket, prefix)
  if known_args.ingest_from == 'local':
    sections = [known_args.localStorage]
  run(known_args, pipeline_args, sections, prefix)


if __name__ == '__main__':
  main()
