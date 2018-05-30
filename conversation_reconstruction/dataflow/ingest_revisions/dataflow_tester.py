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

Dataflow Tester

A unit test on ingesting Wikipedia xml files to json records.

Run with:

python dataflow_tester.py

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from dataflow_main import WriteDecompressedFile

import json

import tempfile
import logging
import unittest
import hashlib
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import SetupOptions

from apache_beam.testing.test_pipeline import TestPipeline
from apache_beam.testing.util import open_shards 
from apache_beam.testing.util import equal_to
from apache_beam.testing.test_utils import compute_hash

class TestParDo(unittest.TestCase):
    def create_temp_file(self):
      with tempfile.NamedTemporaryFile(delete=False) as f:
        return f.name

    def test_pardo(self):
      pipeline_args = [
        '--runner=DirectRunner',
        '--project=wikidetox-viz',
        '--staging_location=gs://wikidetox-viz-dataflow/staging',
        '--temp_location=gs://wikidetox-viz-dataflow/tmp',
        '--job_name=test-ingestion-pipeline', 
        '--num_workers=30',
      ]
      test_url  = [json.dumps(('http://dumps.wikimedia.your.org/chwiki/latest/', 'chwiki-latest-pages-meta-history.xml.7z'))]
      ans_hash = "8f32f3812f123411dafe9e715e34477df26d434e"
      temp_path = self.create_temp_file()

      pipeline_options = PipelineOptions(pipeline_args)
      pipeline_options.view_as(SetupOptions).save_main_session = True
      with TestPipeline(options=pipeline_options) as p:
        p = (p | beam.Create(test_url)
               | beam.ParDo(WriteDecompressedFile(), 'latest', 'ch')
               | beam.Map(lambda x: json.dumps(x['rev_id']))
               | beam.io.WriteToText("%s"%temp_path, num_shards=1))
      results = []
      with open("%s-00000-of-00001"%temp_path) as result_file:
        for line in result_file:
          results.append(line[:-1])
      self.assertEqual(len(results), 776)
      results = sorted(results)
      m = hashlib.new("sha1")
      for elem in results:
          m.update(str(elem))
      self.assertEqual(m.hexdigest(), ans_hash)

if __name__ == '__main__':
   logging.getLogger().setLevel(logging.INFO)
   unittest.main()
