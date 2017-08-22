"""
A dataflow pipeline to reconstruct conversations on Wikipedia talk pages from ingested json files.

Run with:

python dataflow_main.py --setup_file ./setup.py
"""
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import (
         bytes, dict, int, list, object, range, str,
         ascii, chr, hex, input, next, oct, open,
         pow, round, super,
         filter, map, zip)

import argparse
import logging
import subprocess
import json
from os import path
from construct_utils import constructing_pipeline

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import SetupOptions
from apache_beam.io import ReadFromText
from apache_beam.io import WriteToText
from google.cloud import storage
import traceback


def run(arg_dict):
  """Main entry point; defines and runs the wordcount pipeline."""

  parser = argparse.ArgumentParser()
  parser.add_argument('--input',
                      dest='input',
                      default=arg_dict.pop('input'),
                      help='Input file to process.')
  parser.add_argument('--output',
                      dest='output',
                      # CHANGE 1/5: The Google Cloud Storage path is required
                      # for outputting the results.
                      default=arg_dict.pop('output'),
                      help='Output file to write results to.')
  argv = ['--%s=%s' % (k,v) for k,v in arg_dict.items()]
  known_args, pipeline_args = parser.parse_known_args()

  # We use the save_main_session option because one or more DoFn's in this
  # workflow rely on global context (e.g., a module imported at module level).
  pipeline_options = PipelineOptions(pipeline_args)
  pipeline_options.view_as(SetupOptions).save_main_session = True
  with beam.Pipeline(options=pipeline_options) as p:

    # Read the text file[pattern] into a PCollection.
    filenames = (p | 'ReadFromText' >> beam.io.ReadFromText(known_args.input)
                   | beam.ParDo(ReconstructConversation())
                   | WriteToText(known_args.output))

class ReconstructConversation(beam.DoFn):
  def process(self, element):
    page = json.loads(element)
    logging.info('USERLOG: Working on %s' % page['page_id'])
    page_id = page['page_id']
    status = 'NO STATUS'

    local_out_filename = page_id + '.json'
    out_file_path = 'gs://wikidetox-viz-dataflow/conversations/'

    check_file_cmd = (['gsutil', '-q', 'stat', path.join(out_file_path, local_out_filename)])
    file_not_exist = subprocess.call(check_file_cmd)
    if '/Archive' in page['page_title']:
       logging.info('USERLOG: SKIPPED FILE %s as it is an archived talk page.' % page_id)
       status = 'ARCHIVE PAGE'
    if(file_not_exist and not(status == 'ARCHIVE PAGE')):
      try:
        logging.info('USERLOG: Loading constructor with input: %s output: %s' % (page_id, local_out_filename))
        processor = constructing_pipeline.ConstructingPipeline(page, local_out_filename)
        logging.info('USERLOG: Running constructor on %s.' % page_id)
        processor.run_constructor()

        logging.info('USERLOG: Running gsutil cp %s %s' % (local_out_filename, out_file_path))
        cp_remote_cmd = (['gsutil', 'cp', local_out_filename, out_file_path])
        cp_proc = subprocess.call(cp_remote_cmd)
        if cp_proc == 0:
          status = 'SUCCESS'
        else:
          status = 'FAILED to copy to remote'

        logging.info('USERLOG: Removing local files.')
        rm_cmd = (['rm', local_out_filename])
        subprocess.call(rm_cmd)
        rm_cmd = (['rm', chunk_name])
        subprocess.call(rm_cmd)

        logging.info('USERLOG: Job complete on %s.' % page_id)

      except:
        logging.info('USERLOG: Hit unknown exception on %s.' % page_id)
        status = 'FAILED with Unknown Exception'
    else:
      logging.info('USERLOG: SKIPPED FILE %s as it is already processed.' % page_id)
      status = 'ALREADY EXISTS'

    return "%s %s" % (chunk_name, status)

if __name__ == '__main__':
  logging.getLogger().setLevel(logging.INFO)
  with open("args_config.json") as f:
    arg_dict = json.loads(f.read())
  run(arg_dict)



