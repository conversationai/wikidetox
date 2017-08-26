"""
A dataflow pipeline to ingest the Wikipedia dump from 7zipped xml files to json.

Run with:

python dataflow_main.py --setup_file ./setup.py
"""

from __future__ import absolute_import

import argparse
import logging
import subprocess
import json
from os import path
import xml.sax
from ingest_utils import wikipedia_revisions_ingester as wiki_ingester

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import SetupOptions
from apache_beam.io import ReadFromText
from apache_beam.io import WriteToText
from google.cloud import storage



def run(argv = None):
  """Main entry point; defines and runs the wordcount pipeline."""

  parser = argparse.ArgumentParser()
  parser.add_argument('--input',
                      dest='input',
                      default='gs://wikidetox-viz-dataflow/input_lists/7z_file_list_short.txt',
                      help='Input file to process.')
  parser.add_argument('--output',
                      dest='output',
                      default='gs://wikidetox-viz-dataflow/output_lists/ingested_sharded/talk_pages.json',
                      help='Output file to write results to.')
  known_args, pipeline_args = parser.parse_known_args(argv)
  pipeline_args.extend([
    '--runner=DataflowRunner',
    '--project=wikidetox-viz',
    '--staging_location=gs://wikidetox-viz-dataflow/staging',
    '--temp_location=gs://wikidetox-viz-dataflow/tmp',
    '--job_name=nthain-test-job',
    '--num_workers=5',
  ])

  pipeline_options = PipelineOptions(pipeline_args)
  pipeline_options.view_as(SetupOptions).save_main_session = True
  with beam.Pipeline(options=pipeline_options) as p:

    filenames = (p | ReadFromText(known_args.input)
                   | beam.ParDo(WriteDecompressedFile())
                   | WriteToText(known_args.output))

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
    ingest_proc = subprocess.Popen(ingestion_cmd, stdout=subprocess.PIPE, bufsize = 4096)

    for line in ingest_proc.stdout:
      yield line

if __name__ == '__main__':
  logging.getLogger().setLevel(logging.INFO)
  run()

