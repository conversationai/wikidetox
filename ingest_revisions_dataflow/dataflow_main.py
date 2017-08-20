"""
A dataflow pipeline to ingest the Wikipedia dump from 7zipped xml files to json.

Run with:

python dataflow_main.py --setup_file ./setup.py
"""

from __future__ import absolute_import

import argparse
import logging

import apache_beam as beam
from ingest_utils import wikipedia_revisions_ingester as wiki_ingester
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import SetupOptions
from apache_beam.io import ReadFromText
from google.cloud import storage
import subprocess


def run(argv=None):
  """Main entry point; defines and runs the wordcount pipeline."""

  parser = argparse.ArgumentParser()
  parser.add_argument('--input',
                      dest='input',
                      default='gs://wikidetox-viz-dataflow/input_lists/7z_file_list.txt',
                      help='Input file to process.')
  parser.add_argument('--output',
                      dest='output',
                      # CHANGE 1/5: The Google Cloud Storage path is required
                      # for outputting the results.
                      default='ingested/',
                      help='Output file to write results to.')
  known_args, pipeline_args = parser.parse_known_args(argv)
  pipeline_args.extend([
      # CHANGE 2/5: (OPTIONAL) Change this to DataflowRunner to
      # run your pipeline on the Google Cloud Dataflow Service.
      '--runner=DataflowRunner',
      # CHANGE 3/5: Your project ID is required in order to run your pipeline on
      # the Google Cloud Dataflow Service.
      '--project=wikidetox-viz',
      # CHANGE 4/5: Your Google Cloud Storage path is required for staging local
      # files.
      '--staging_location=gs://wikidetox-viz-dataflow/staging',
      # CHANGE 5/5: Your Google Cloud Storage path is required for temporary
      # files.
      '--temp_location=gs://wikidetox-viz-dataflow/tmp',
      '--job_name=nthain-ingest-job-2',
      '--worker_machine_type=n1-highmem-4',
      '--num_workers=6',
  ])

  # We use the save_main_session option because one or more DoFn's in this
  # workflow rely on global context (e.g., a module imported at module level).
  pipeline_options = PipelineOptions(pipeline_args)
  pipeline_options.view_as(SetupOptions).save_main_session = True
  with beam.Pipeline(options=pipeline_options) as p:

    # Read the text file[pattern] into a PCollection.
    filenames = (p | ReadFromText(known_args.input)
                   | beam.ParDo(WriteDecompressedFile()))

class WriteDecompressedFile(beam.DoFn):
  def process(self, element):
    logging.info('USERLOG: Working on %s' % element)
    chunk_name = element

    CLOUD_STORAGE_BUCKET = 'wikidetox-viz-dataflow' # Should be deletable
    OUT_PATH = 'ingested/' # Should be deletable

    in_file_path = 'gs://wikidetox-viz-dataflow/raw-downloads/' + chunk_name
    local_out_filename = chunk_name[:-3] + '.json'
    out_file_path = 'gs://wikidetox-viz-dataflow/ingested/'

    check_file_cmd = (['gsutil', '-q', 'stat', out_file_path + local_out_filename])
    file_not_exist = subprocess.call(check_file_cmd)
    
    if(file_not_exist):
      logging.info('USERLOG: Running gsutil %s ./' % in_file_path)
      cp_local_cmd = (['gsutil', 'cp', in_file_path, './'])
      subprocess.call(cp_local_cmd)

      logging.info('USERLOG: Loading ingester with input: %s output: %s' % (chunk_name, local_out_filename))
      ingester = wiki_ingester.WikipediaRevisionsIngester(chunk_name, local_out_filename)
      logging.info('USERLOG: Running ingester on %s.' % chunk_name)
      ingester.run_ingester()
    
      logging.info('USERLOG: Running gsutil cp %s %s' % ('./' + local_out_filename, out_file_path))
      cp_remote_cmd = (['gsutil', 'cp', './' + local_out_filename, out_file_path])
      subprocess.call(cp_remote_cmd)

      logging.info('USERLOG: Removing local files.')
      rm_cmd = (['rm', './' + local_out_filename])
      subprocess.call(rm_cmd)
      rm_cmd = (['rm', './' + chunk_name])
      subprocess.call(rm_cmd)

      logging.info('USERLOG: Job complete on %s.' % chunk_name)

    else:
      logging.info('USERLOG: SKIPPED FILE %s as it is already ingested.' % chunk_name)

    return element

if __name__ == '__main__':
  logging.getLogger().setLevel(logging.INFO)
  run()


# TODO:
# (1) Clean up code, rename variables, etc.
# (2) Check that no lines were skipped? 
