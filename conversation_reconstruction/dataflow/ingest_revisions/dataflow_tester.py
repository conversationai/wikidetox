"""TODO(yiqingh): DO NOT SUBMIT without one-line documentation for dataflow_tester.

TODO(yiqingh): DO NOT SUBMIT without a detailed description of dataflow_tester.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from dataflow_main import WriteDecompressedFile

import tempfile
import logging
import unittest
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
      test_url  = [('http://dumps.wikimedia.your.org/chwiki/latest/', 'chwiki-latest-pages-meta-history.xml.7z')]
      ans_hash = "81e1986b6bec05866ece6e7cd3cde1d9c66a261f"
      temp_path = self.create_temp_file()

      pipeline_options = PipelineOptions(pipeline_args)
      pipeline_options.view_as(SetupOptions).save_main_session = True
      with TestPipeline(options=pipeline_options) as p:
        p = (p | beam.Create(test_url)
               | beam.ParDo(WriteDecompressedFile())
               | beam.Map(lambda x: json.dumps(x))
               | beam.io.WriteToText("%s"%temp_path, num_shards=1))
        results = []
        with open(temp_path + '.test') as result_file:
          for line in result_file:
              results.append(line)
        print(len(results))
        ans = compute_hash(results)
        self.assertEqual(ans, ans_hash)

if __name__ == '__main__':
   logging.getLogger().setLevel(logging.INFO)
   unittest.main()
