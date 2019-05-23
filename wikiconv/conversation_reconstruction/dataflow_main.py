# -*- coding: utf-8 -*-
# Copyright 2017 Google Inc.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
r"""A dataflow pipeline to reconstruct conversations on Wikipedia talk pages from ingested json files.

Run on local test data with:

```
# Run locally:
python dataflow_main.py \
  --setup_file ./setup.py \
  --input_state './testdata/empty_init_state' \
  --input_revisions './testdata/edgecases_28_convs/revs*' \
  --output_state ./tmp/ \
  --output_conversations ./tmp/ \
  --runner DirectRunner

# Run on the cloud with:
python dataflow_main.py \
  --setup_file ./setup.py \
  --input_state 'gs://YOUR_BUCKET/PATH_TO_INIT_STATE' \
  --input_revisions 'gs://YOUR_BUCKET/PATH_TO_REVS*' \
  --output_state 'gs://YOUR_BUCKET/PATH_TO_OUTPUT_STATE_TO' \
  --output_conversations 'gs://YOUR_BUCKET/PATH_TO_OUTPUT_CONVS_TO' \
  --runner DirectRunner
  --project $YOUR_GCLOUD_PROJECT \
  --job_name $NAME_OF_YOUR_JOB
  --num_workers $NUMBER_OF_WORKERS_SUCH_AS_80
```

Note: Don't forget the quotes on the local paths, otherwise bash will interpret
them and dataflow fails to see all the files.
TODO(ldixon): make the input parser smarter so that it can handle this.

"""
from __future__ import absolute_import
import argparse
import json
import logging
from os import path
import sys
import time

import apache_beam as beam
from apache_beam.io import filesystems
from apache_beam.metrics.metric import Metrics
from apache_beam.metrics.metric import MetricsFilter
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import SetupOptions
from construct_utils import reconstruct_conversation

CUMULATIVE_REVISION_SIZE_THERESHOLD = 250 * 1024 * 1024

# Constants used
SAVE_TO_MEMORY = 0
SAVE_TO_STORAGE = 1

# Number of times to DataFlow should retry a failed worker.
RETRY_LIMIT = 10

# Custom logging level so we don't have to read all the info messages, but we
# see our printed summary statistics.
LOG_LEVEL_OUTPUT_INFO = 25


def page_indexed_metadata_of_revstring(rev_string):
  record_size = len(rev_string)
  record = json.loads(rev_string)
  return (record['page_id'], {
      'page_id': record['page_id'],
      'rev_id': record['rev_id'],
      'timestamp': record['timestamp'],
      'record_size': record_size
  })


def index_by_page_id(s):
  """Pair a dict with a page_id key, pair the page_id with the dict.

  Args:
    s: a dict as a JSON document.

  Returns:
    a tuple of page_id, and parsed Python dict.
  """
  d = json.loads(s)
  return (d['page_id'], d)


def index_by_rev_id(s):
  """Pair a rev_id with a JSON string.

  Args:
    s: a JSON dict.

  Returns:
    A tuple of rev_id and the unparsed JSON string.
  """
  return (json.loads(s)['rev_id'], s)


def get_counter_metric(result, counter_name):
  metrics_filter = MetricsFilter().with_name(counter_name)
  query_result = result.metrics().query(metrics_filter)
  if query_result['counters']:
    return query_result['counters'][0].committed
  else:
    return None


def get_distributions_metric(result, counter_name):
  metrics_filter = MetricsFilter().with_name(counter_name)
  query_result = result.metrics().query(metrics_filter)
  if query_result['distributions']:
    return query_result['distributions'][0].committed
  else:
    return None


# TODO(ldixon): pull these into a class, and output to JSON as a job
# summary for better debugging.
def print_metrics(result):
  """Print metrics we might be interested in.

  Args:
    result: dataflow result.
  """
  logging.log(LOG_LEVEL_OUTPUT_INFO,
              '------------------------------------------------')
  logging.log(LOG_LEVEL_OUTPUT_INFO, ' KEY METRICS: ')
  logging.log(LOG_LEVEL_OUTPUT_INFO,
              '------------------------------------------------')
  logging.log(LOG_LEVEL_OUTPUT_INFO, '* pages_count: %d',
              get_counter_metric(result, 'pages_count'))
  logging.log(LOG_LEVEL_OUTPUT_INFO, '* revisions_count: %d',
              get_counter_metric(result, 'revisions_count'))
  logging.log(LOG_LEVEL_OUTPUT_INFO, '* very_long_page_histories_count: %d',
              get_counter_metric(result, 'very_long_page_histories_count'))
  revisions_per_page_distr = get_distributions_metric(
      result, 'revisions_per_page_distr')
  logging.log(LOG_LEVEL_OUTPUT_INFO, '* revisions_per_page_distr.mean: %d',
              revisions_per_page_distr.mean)
  logging.log(LOG_LEVEL_OUTPUT_INFO, '* revisions_per_page_distr.sum: %d',
              revisions_per_page_distr.sum)
  cumulative_page_rev_size_distr = get_distributions_metric(
      result, 'cumulative_page_rev_size_distr')
  logging.log(LOG_LEVEL_OUTPUT_INFO,
              '* cumulative_page_rev_size_distr.mean: %d',
              cumulative_page_rev_size_distr.mean)
  logging.log(LOG_LEVEL_OUTPUT_INFO, '* cumulative_page_rev_size_distr.sum: %d',
              cumulative_page_rev_size_distr.sum)


def run(locations, run_pipeline_args, storage_client,
        cumulative_revision_size_threshold):
  """Main entry point; runs the reconstruction pipeline.

  Args:
    locations: Locations instance with the various input/output locations.
    run_pipeline_args: flags for PipelineOptions, detailing how to run the job.
      See https://cloud.google.com/dataflow/pipelines/specifying-exec-params
    storage_client: if not None contains the cloud storage client.
    cumulative_revision_size_threshold: the size at which cloud storage is used
      instead of memory.
  """
  run_pipeline_args.extend([
      '--staging_location={dataflow_staging}'.format(
          dataflow_staging=locations.dataflow_staging),
      '--temp_location={dataflow_temp}'.format(
          dataflow_temp=locations.dataflow_temp),
  ])
  pipeline_options = PipelineOptions(run_pipeline_args)
  # TODO(ldixon): investigate why/where we use global objects, and remove them
  # by adding them as command line arguments/config.
  # See: https://cloud.google.com/dataflow/faq#how-do-i-handle-nameerrors
  pipeline_options.view_as(SetupOptions).save_main_session = True

  with beam.Pipeline(options=pipeline_options) as p:
    # Find which revisions are from pages with histories so long we'll need to
    # process them on disk instead of in memory.
    # TODO(ldixon): probably better to simply extend the meta-data with a mark
    # for its part of a big page.
    rev_marks = (
        p
        | 'input_revisions-for-metadata' >> beam.io.ReadFromText(
            locations.input_revisions)
        |
        'metadata_of_revstring' >> beam.Map(page_indexed_metadata_of_revstring)
        | beam.GroupByKey()
        | beam.ParDo(
            MarkRevisionsOfBigPages(cumulative_revision_size_threshold)))
    raw_revision_ids = (
        p
        | 'input_revisions' >> beam.io.ReadFromText(locations.input_revisions)
        | 'input_revisions-by-rev_id' >> beam.Map(index_by_rev_id))
    revs_with_marks_by_id = (
        {
            'metadata': rev_marks,
            'raw': raw_revision_ids
        }
        | 'GroupbyRevID' >> beam.CoGroupByKey()
        | 'output_revs_with_marks' >> beam.ParDo(
            WriteToStorage(), locations.output_revs_with_marks))
    last_revisions = (
        p
        | 'input_last_revisions' >> beam.io.ReadFromText(
            locations.input_last_revisions)
        | 'input_last_revisions-by-page_id' >> beam.Map(index_by_page_id))
    page_state = (
        p
        |
        'input_page_states' >> beam.io.ReadFromText(locations.input_page_states)
        | 'input_page_states-by-page_id' >> beam.Map(index_by_page_id))
    error_log = (
        p
        | 'input_error_logs' >> beam.io.ReadFromText(locations.input_error_logs)
        | 'input_error_logs-by-page_id' >> beam.Map(index_by_page_id))

    # Main Pipeline
    reconstruction_results, page_states, last_rev_output, error_log = (
        {
            'to_be_processed': revs_with_marks_by_id,
            'last_revision': last_revisions,
            'page_state': page_state,
            'error_log': error_log
        }
        # Join information based on page_id.
        | 'GroupBy_page_id' >> beam.CoGroupByKey()
        | beam.ParDo(
            reconstruct_conversation.ReconstructConversation(storage_client),
            locations.output_revs_with_marks).with_outputs(
                'page_states',
                'last_revision',
                'error_log',
                main='reconstruction_results'))
    # Main Result
    # pylint:disable=expression-not-assigned
    reconstruction_results | 'output_conversations' >> beam.io.WriteToText(
        locations.output_conversations)

    # Saving intermediate results to separate locations.
    page_states | 'output_page_states' >> beam.io.WriteToText(
        locations.output_page_states)
    last_rev_output | 'output_last_revisions' >> beam.io.WriteToText(
        locations.output_last_revisions)
    error_log | 'output_error_logs' >> beam.io.WriteToText(
        locations.output_error_logs)

    result = p.run()
    result.wait_until_finish()
    if (not hasattr(result, 'has_job')  # direct runner
        or result.has_job):  # not just a template creation
      print_metrics(result)


# TODO(ldixon): Instead of requiring the history of a page's revisions'
# meta-data to fit in memory to be counted, we could instead tag the pages that
# are too big by simply streaming revisions for each page, counting as we go,
# and then re-joining to the page-ids to then re-tag the stream of revisions.
class MarkRevisionsOfBigPages(beam.DoFn):
  """A DoFn that paritions pages with large sized revisions into buckets."""

  def __init__(self, cumulative_revision_size_threshold):
    """Constructor.

    Args:
      cumulative_revision_size_threshold: The max cumulative size of a page's
        revisions to be considered to try and  keep in memory when processing.
        Measured by python string length. approx 250 MB
    """
    self.very_long_page_histories_count = Metrics.counter(
        self.__class__, 'very_long_page_histories_count')
    self.pages_count = Metrics.counter(self.__class__, 'pages_count')
    self.revisions_count = Metrics.counter(self.__class__, 'revisions_count')
    self.revisions_per_page_distr = Metrics.distribution(
        self.__class__, 'revisions_per_page_distr')
    self.cumulative_page_rev_size_distr = Metrics.distribution(
        self.__class__, 'cumulative_page_rev_size_distr')
    self.cumulative_revision_size_threshold = cumulative_revision_size_threshold

  def process(self, (page_id, metadata)):
    flag = SAVE_TO_MEMORY
    metadata = list(metadata)
    # Update metrics.
    self.pages_count.inc()
    revisions_for_this_page = len(metadata)
    self.revisions_count.inc(revisions_for_this_page)
    self.revisions_per_page_distr.update(revisions_for_this_page)
    # Hack to make sure its defined.
    self.very_long_page_histories_count.inc(0)

    revision_size_sum = 0
    for s in metadata:
      revision_size_sum += s['record_size']
    self.cumulative_page_rev_size_distr.update(revision_size_sum)
    if revision_size_sum > self.cumulative_revision_size_threshold:
      flag = SAVE_TO_STORAGE
      self.very_long_page_histories_count.inc()
    for rev in metadata:
      yield (rev['rev_id'], flag)


class WriteToStorage(beam.DoFn):
  """Beam DoFn for writing dictionaries to memory or files."""

  def __init__(self):
    self.revisions_to_storage = Metrics.counter(self.__class__,
                                                'revisions_to_storage')
    self.write_retries = Metrics.counter(self.__class__, 'write_retries')

  def process(self, element, outputdir):
    (rev_id, data) = element
    metadata = data['metadata'][0]
    raw = data['raw'][0]
    if metadata == SAVE_TO_MEMORY:
      logging.info('USERLOG: Write to memory.')
      ret = json.loads(raw)
      page_id = ret['page_id']
      ret['rev_id'] = int(ret['rev_id'])
    else:
      element = json.loads(raw)
      page_id = element['page_id']
      rev_id = element['rev_id']
      self.revisions_to_storage.inc()
      # Creates writing path given the week, year pair
      write_path = path.join(outputdir, page_id + '_' + rev_id)
      # Writes to storage
      logging.info('USERLOG: Write to path %s.', write_path)
      wait_time = 1
      for _ in range(RETRY_LIMIT):
        try:
          with filesystems.FileSystems.create(write_path) as outputfile:
            json.dump(element, outputfile)
        except RuntimeError:
          self.write_retries.inc()
          time.sleep(wait_time)
          wait_time *= 2
        else:
          break
      ret = {'timestamp': element['timestamp'], 'rev_id': int(rev_id)}
    yield (page_id, ret)


class Locations(object):
  """A simple class to construct the various locations.

  Constructs locations, which can be file paths, google
  cloud storage bucket paths, or other locations readable by Google Cloud
  DataFlow.
  """

  def __init__(self, loc_known_args):
    self.input_revisions = loc_known_args.input_revisions
    self.input_last_revisions = (
        loc_known_args.input_state + '/last_revisions/last_rev*')
    self.input_page_states = (
        loc_known_args.input_state + '/page_states/page_states*')
    # TODO(ldixon): why do we take in errors? remove?
    self.input_error_logs = (
        loc_known_args.input_state + '/error_logs/error_log*')

    self.dataflow_staging = (
        loc_known_args.output_state + '/dataflow_tmp/staging/')
    self.dataflow_temp = (loc_known_args.output_state + '/dataflow_tmp/temp/')

    self.output_revs_with_marks = (
        loc_known_args.output_state + '/revs_with_marks')
    self.output_page_states = (
        loc_known_args.output_state + '/page_states/page_states')
    self.output_last_revisions = (
        loc_known_args.output_state + '/last_revisions/last_rev')
    self.output_error_logs = (
        loc_known_args.output_state + '/error_logs/error_log')

    self.output_conversations = (
        loc_known_args.output_conversations + '/conversations')


def main(argv):
  logging.getLogger().setLevel(LOG_LEVEL_OUTPUT_INFO)
  parser = argparse.ArgumentParser()
  parser.add_argument(
      '--input_state',
      dest='input_state',
      help='Location of input page state to start from.')
  parser.add_argument(
      '--input_revisions',
      dest='input_revisions',
      help='Location of the input revisions to process.')
  parser.add_argument(
      '--output_state',
      dest='output_state',
      help='Location for intermediate outputs.')
  parser.add_argument(
      '--output_conversations',
      dest='output_conversations',
      help='Location to output conversations.')

  # All unknown flags are considered to be pipeline arguments.
  known_args, pipeline_args = parser.parse_known_args(argv)
  run(Locations(known_args), pipeline_args, None, 250 * 1024 * 1204)


if __name__ == '__main__':
  main(sys.argv[1:])
