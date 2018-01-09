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
import urllib2
import traceback

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import SetupOptions
from apache_beam.io.gcp import bigquery as bigquery_io 

def run(known_args, pipeline_args):
  """Main entry point; defines and runs the reconstruction pipeline."""

  pipeline_args.extend([
    '--runner=DataflowRunner',
    '--project=wikidetox-viz',
    '--staging_location=gs://wikidetox-viz-dataflow/staging',
    '--temp_location=gs://wikidetox-viz-dataflow/tmp',
    '--job_name=yiqing-reconstruction-test',
    '--num_workers=30',
  ])


  pipeline_options = PipelineOptions(pipeline_args)
  with beam.Pipeline(options=pipeline_options) as p:

    # Read the text file[pattern] into a PCollection.
    filenames = (p | beam.io.Read(beam.io.BigQuerySource(query='SELECT UNIQUE(page_id) as page_id FROM [%s]'%known_args.input_table, validate=True)) 
                   | beam.ParDo(ReconstructConversation())
                   | beam.io.Write(bigquery_io.BigQuerySink(known_args.output_table, schema=known_args.output_schema, validate=True)))

class ReconstructConversation(beam.DoFn):
  def process(self, row):

#    from construct_utils import constructing_pipeline
    import logging
    from google.cloud import bigquery as bigquery_op 
    input_table = "wikidetox_conversations.test_page_3_issue21" 

    logging.info('USERLOG: Work start')
    page_id = row['page_id']
    client = bigquery_op.Client(project='wikidetox-viz')
    query = ("SELECT rev_id FROM %s WHERE page_id = \"%s\""%(input_table, page_id))
    query_job = client.query(query)
    rev_ids = []
    for row in query_job.result():
        rev_ids.append(row.rev_id)

    construction_cmd = ['python2', '-m', 'construct_utils.run_constructor', '--table', input_table, '--revisions', rev_ids]
    ingest_proc = subprocess.Popen(construction_cmd, stdout=subprocess.PIPE, bufsize = 4096)

#    page = json.loads(element)
#    logging.info('USERLOG: Working on %s' % page['page_id'])
#    page_id = page['page_id']
#    status = 'NO STATUS'
#
#    local_out_filename = page_id + '.json'
#    out_file_path = 'gs://wikidetox-viz-dataflow/conversations/'
#
#    check_file_cmd = (['gsutil', '-q', 'stat', path.join(out_file_path, local_out_filename)])
#    file_not_exist = subprocess.call(check_file_cmd)
#    if '/Archive' in page['page_title']:
#       logging.info('USERLOG: SKIPPED FILE %s as it is an archived talk page.' % page_id)
#       status = 'ARCHIVE PAGE'
#    if(file_not_exist and not(status == 'ARCHIVE PAGE')):
#      try:
#        logging.info('USERLOG: Loading constructor with input: %s output: %s' % (page_id, local_out_filename))
#        processor = constructing_pipeline.ConstructingPipeline(page, local_out_filename)
#        logging.info('USERLOG: Running constructor on %s.' % page_id)
#        processor.run_constructor()
#
#        logging.info('USERLOG: Running gsutil cp %s %s' % (local_out_filename, out_file_path))
#        cp_remote_cmd = (['gsutil', 'cp', local_out_filename, out_file_path])
#        cp_proc = subprocess.call(cp_remote_cmd)
#        if cp_proc == 0:
#          status = 'SUCCESS'
#        else:
#          status = 'FAILED to copy to remote'
#
#        logging.info('USERLOG: Removing local files.')
#        rm_cmd = (['rm', local_out_filename])
#        subprocess.call(rm_cmd)
#        rm_cmd = (['rm', chunk_name])
#        subprocess.call(rm_cmd)
#
#        logging.info('USERLOG: Job complete on %s.' % page_id)
#
#      except:
#        logging.info('USERLOG: Hit unknown exception on %s.' % page_id)
#        status = 'FAILED with Unknown Exception'
#    else:
#      logging.info('USERLOG: SKIPPED FILE %s as it is already processed.' % page_id)
#      status = 'ALREADY EXISTS'
#
#    return 

if __name__ == '__main__':
  logging.getLogger().setLevel(logging.INFO)
  parser = argparse.ArgumentParser()
  # Input BigQuery Table
  input_schema = 'sha1:STRING,user_id:STRING,format:STRING,user_text:STRING,timestamp:STRING,text:STRING,page_title:STRING,model:STRING,page_namespace:STRING,page_id:STRING,rev_id:STRING,comment:STRING, user_ip:STRING, truncated:BOOLEAN,records_count:INTEGER,record_index:INTEGER'
  parser.add_argument('--input_table',
                      dest='input_table',
                      default='wikidetox-viz:wikidetox_conversations.test_page_3_issue21',
                      help='Input table for reconstruction.')
  parser.add_argument('--input_schema',
                      dest='input_schema',
                      default=input_schema,
                      help='Input table schema.')
  # Ouput BigQuery Table
  output_schema = 'sha1:STRING,user_id:STRING,format:STRING,user_text:STRING,timestamp:STRING,text:STRING,page_title:STRING,model:STRING,page_namespace:STRING,page_id:STRING,rev_id:STRING,comment:STRING, user_ip:STRING, truncated:BOOLEAN,records_count:INTEGER,record_index:INTEGER'
  parser.add_argument('--output_table',
                      dest='output_table',
                      default='wikidetox-viz:wikidetox_conversations.reconstructed_conversation_test_page_3',
                      help='Output table for reconstruction.')
  parser.add_argument('--output_schema',
                      dest='output_schema',
                      default=output_schema,
                      help='Output table schema.')
  global known_args
  known_args, pipeline_args = parser.parse_known_args()

  run(known_args, pipeline_args)



