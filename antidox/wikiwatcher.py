"""Simple watcher that prints wikipedia changes as they occur."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import json

import sseclient


def log_event(change):
  """Logs event by printing.

  Args:
    change: a json object with the wikimedia change record.
  """
  print(
      u'user:{user} namespace:{namespace} bot:{bot} comment:{comment} title:{title}'
      .format(**change))


def watcher(event_source, wiki_filter, namespaces_filter, callback):
  """Watcher captures and filters evens from mediawiki.

  Args:
    event_source: an interable source of streaming sse events.
    wiki_filter: string for filtering 'wiki' class.
    namespaces_filter: a set() of namespaces to keep.
    callback: A method to invoke with the JSON params for each filterd event.
  """
  for event in event_source:
    if event.event == 'message' and event.data:
      change = json.loads(event.data)
      if change['bot']:
        continue
      if change['wiki'] != wiki_filter:
        continue
      if change['namespace'] not in namespaces_filter:
        continue
      callback(change)


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument(
      '--wiki_filter', default='enwiki', help='Wiki to scan, default enwiki.')
  parser.add_argument(
      '--namespaces',
      default='1,3',
      help='Namespaces defined in http://phabricator.wikimedia.org/source/mediawiki/browse/master/includes/Defines.php separated by commas.'
  )
  parser.add_argument(
      '--url',
      default='https://stream.wikimedia.org/v2/stream/recentchange',
      help='SSE client url')
  args = parser.parse_args()

  namespaces = set([int(ns) for ns in args.namespaces.split(',')])
  client = sseclient.SSEClient(args.url)

  watcher(client, args.wiki_filter, namespaces, log_event)
