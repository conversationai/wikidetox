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

def run(arg_dict=None):
  pipeline_args = ['--project=wikidetox-viz', '--worker_machine_type=n1-standard-1', '--num_workers=1', '--runner=DataflowRunner', '--temp_location=gs://wikidetox-viz-dataflow/tempfiles', '--staging_location=gs://wikidetox-viz-dataflow/stages', '--job_name=yiqing-minimal-test']
  
  # We use the save_main_session option because one or more DoFn's in this
  # workflow rely on global context (e.g., a module imported at module level).
  pipeline_options = PipelineOptions(pipeline_args)
#  pipeline_options.view_as(SetupOptions).save_main_session = True
  with beam.Pipeline(options=pipeline_options) as p:
    # Read the text file[pattern] into a PCollection.
    filenames = (p | "ReadFromJson" >> ReadFromText('gs://wikidetox-viz-dataflow/input_lists/7z_file_list.txt')                   | WriteToText('gs://wikidetox-viz-dataflow/conversations/log'))

if __name__ == '__main__':
  logging.getLogger().setLevel(logging.INFO)
  run()



