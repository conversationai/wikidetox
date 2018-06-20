"""Fetch all revisions from wikipedia given a title of the page.

Args:
title -- The title of the page to fetch.
output_path -- Where to store the output data.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import json
import logging
import os
import time
import requests
import argparse


def rename(record, title):
  """Rename data fields."""
  record['text'] = record['*']
  record['page_title'] = title
  del record['*']
  return record


def get_revision(title):
  """Queries Wikipedia API for revision data given the page id."""
  baseurl = 'http://en.wikipedia.org/w/api.php'
  props = ['ids', 'timestamp', 'user', 'userid', 'sha1', 'comment', 'content']
  atts = {'action': 'query', 'prop': 'revisions', 'rvprop': '|'.join(props),
          'rvlimit': 'max', 'format': 'json', 'titles': title}
  while True:
    response = requests.get(baseurl, params=atts)
    if response.status_code != 429:
      break
    time.sleep(10)
  data = response.json()
  cnt = 0
  for val in data['query']['pages'].values():
    for rev in val['revisions']:
      try:
        # In the case that some revisions are hidden in the API, the
        # collection process skips the revision.
        yield rename(rev, title)
        cnt += 1
      except KeyError:
        pass
  while ('continue' in data and 'rvcontinue' in data['continue']):
    logging.info('PROGRESS LOG: fetching page %s: %d revisions fetched.'
                 , title, cnt)
    atts['rvcontinue'] = data['continue']['rvcontinue']
    while True:
      response = requests.get(baseurl, params=atts)
      if response.status_code != 429:
        break
      time.sleep(10)
    data = response.json()
    for val in data['query']['pages'].values():
      for rev in val['revisions']:
        try:
          yield rename(rev, title)
          cnt += 1
        except KeyError:
          pass


def main(args):
  for r in get_revision(args.title):
    with open(os.path.join(args.output_path, 'test',
                           'revision_%d.json' % r['revid']), 'w') as f:
      json.dump(r, f)
  logging.info('PROGRESS LOG: page %s data fetched.', FLAGS.title)


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  logging.getLogger().setLevel(logging.INFO)
  # input/output parameters.
  parser.add_argument("--title",
                      help="The title of the page to fetch.")
  parser.add_argument("--output_path",
                      default = os.environ['HOME'],
                      help="Where to store the output data.")
  known_args, pipeline_args = parser.parse_known_args()
  run(known_args)
