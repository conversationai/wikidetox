"""Copyright 2017 Google Inc.

Licensed under the Apache License, Version 2.0
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

Dataflow Tester

A unit test on ingesting Wikipedia xml files to json records.

Run with:

python dataflow_tester.py

"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
import os
import sys
import tempfile
import unittest

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import SetupOptions
from apache_beam.testing.test_pipeline import TestPipeline
from bazel_tools.tools.python.runfiles import runfiles
from wikiconv.ingest_revisions import dataflow_main


class TestParDo(unittest.TestCase):

  def init(self):
    pipeline_args = [
        '--runner=DirectRunner',
        '--job_name=test-ingestion-pipeline',
    ]
    test_url = [('http://dumps.wikimedia.your.org/chwiki/latest',
                 'chwiki-latest-pages-meta-history.xml.bz2')]
    return pipeline_args, test_url

  def create_temp_file(self):
    with tempfile.NamedTemporaryFile(delete=False) as f:
      return f.name

  def test_download(self):
    pipeline_args, test_url = self.init()
    temp_path = self.create_temp_file()
    pipeline_options = PipelineOptions(pipeline_args)
    pipeline_options.view_as(SetupOptions).save_main_session = True

    # Test Download
    with TestPipeline(options=pipeline_options) as p:
      p = (
          p | beam.Create(test_url)
          | beam.ParDo(dataflow_main.DownloadDataDumps(),
                       'wikidetox-viz-dataflow', 'test_ingestion')
          | beam.io.WriteToText('%s' % temp_path, num_shards=1))
    results = []
    with open('%s-00000-of-00001' % temp_path) as result_file:
      for line in result_file:
        results.append(line[:-1])
    self.assertEqual(''.join(results),
                     'chwiki-latest-pages-meta-history.xml.bz2')

  def test_ingest(self):
    r = runfiles.Create()
    data = r.Rlocation('__main__/wikiconv/ingest_revisions/testdata/test_wiki_dump.xml.bz2')
    pipeline_args, _ = self.init()
    temp_path = self.create_temp_file()
    pipeline_options = PipelineOptions(pipeline_args)
    pipeline_options.view_as(SetupOptions).save_main_session = True
    # Test Ingestion
    with TestPipeline(options=pipeline_options) as p:
      p = (
          p | beam.Create([data])
          | beam.ParDo(dataflow_main.WriteDecompressedFile(), None,
                       'wikidetox-viz-dataflow', 'local')
          | beam.io.WriteToText('%s' % temp_path, num_shards=1))
    results = []
    with open('%s-00000-of-00001' % temp_path) as result_file:
      for line in result_file:
        results.append(line[:-1])
    self.assertEqual(len(results), 5)


if __name__ == '__main__':
  logging.getLogger().setLevel(logging.INFO)
  unittest.main()
