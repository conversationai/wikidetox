"""
A dataflow pipeline to reconstruct conversations on Wikipedia talk pages from ingested json files.

Run with:

python dataflow_main.py --setup_file ./setup.py
"""
from __future__ import absolute_import
import argparse
import logging
import subprocess
import json
from os import path

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import SetupOptions
from apache_beam.io import ReadFromText
from apache_beam.io import WriteToText
from google.cloud import storage
import traceback


def run(known_args, pipeline_args):
  """Main entry point; defines and runs the reconstruction pipeline."""

  pipeline_options = PipelineOptions(pipeline_args)
  with beam.Pipeline(options=pipeline_options) as p:

    # Read the text file[pattern] into a PCollection.
    filenames = (p | ReadFromText(known_args.input)
                   | beam.ParDo(ReconstructConversation())
                   | beam.io.Write(bigquery.BigQuerySink(known_args.output_table, schema=known_args.schema, validate=True)))

class ReconstructConversation(beam.DoFn):
  def process(self, element):

    from construct_utils import constructing_pipeline
    import logging
    import json

    logging.info('USERLOG: Work start')

    return 
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

    return 

if __name__ == '__main__':
  logging.getLogger().setLevel(logging.INFO)
  parser = argparse.ArgumentParser()
  # Input BigQuery Table
  input_schema = 'sha1:STRING,user_id:STRING,format:STRING,user_text:STRING,timestamp:STRING,text:STRING,page_title:STRING,model:STRING,page_namespace:STRING,page_id:STRING,rev_id:STRING,comment:STRING, user_ip:STRING, truncated:BOOLEAN,records_count:INTEGER,record_index:INTEGER'
  parser.add_argument('--input_table',
                      dest='input_table',
                      default='wikidetox-viz:wikidetox_conversations.ingested_conversations_stuck',
                      help='Input table for reconstruction.')
  parser.add_argument('--input_schema',
                      dest='input_schema',
                      default=input_schema,
                      help='Input table schema.')

  known_args, pipeline_args = parser.parse_known_args()

  run(known_args, pipeline_args)



