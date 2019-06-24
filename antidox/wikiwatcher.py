"""Simple watcher that prints wikipedia changes as they occur."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import pprint
import argparse
import requests
import sseclient
from googleapiclient import errors as google_api_errors

from antidox import clean
from antidox import perspective


# pylint: disable=fixme, too-many-locals
def log_event(apikey_data, toxicity, dlp, change):
  """Logs event by printing.

  Args:
    change: a json object with the wikimedia change record.
  """
  # print(
  #     u'user:{user} namespace:{namespace} bot:{bot} comment:{comment} title:{title}'
  #     .format(**change))
  # print('\n########## change:')
  from_id = (str(change['revision']['old']))
  to_id = (str(change['revision']['new']))
  page = ("https://en.wikipedia.org/w/api.php?action=compare&fromrev="
          + from_id + "&torev=" + to_id + "&format=json")
  get_page = requests.get(page)
  response = json.loads(get_page.content)
  revision = response['compare']['*']

  text = clean.content_clean(revision)

  # for line in text:
  pii_results = open("pii_results.txt", "a+")
  toxicity_results = open("toxicity_results.txt", "a+")
  print(text)
  if not text:
    return
  dlp_response = perspective.dlp_request(dlp, apikey_data, text)
  try:
    perspective_response = perspective.perspective_request(toxicity, text)
  # Perspective can't handle language errors at this time
  except google_api_errors.HttpError as err:
    print("Error:", err)
    return
  has_pii_bool, pii_type = perspective.contains_pii(dlp_response)
  if has_pii_bool:
    pii_results.write(u'user:{user} namespace:{namespace} bot:{bot} comment:{comment}'+
                      'title:{title}'.format(**change)+"\n"+str(text)+"\n"+'contains pii?'
                      +"Yes"+"\n"
                      +str(pii_type)+"\n"
                      +"==============================================="+"\n")
  if perspective.contains_toxicity(perspective_response):
    toxicity_results.write(u'user:{user} namespace:{namespace} bot:{bot} comment:{comment}'+
                           'title:{title}'.format(**change)+"\n"+str(text)+"\n"
                           +"contains TOXICITY?:"+"Yes"+"\n"+
                           str(perspective_response['attributeScores']
                               ['TOXICITY']['summaryScore']['value'])+"\n"
                           +"=========================================="+"\n")
  toxicity_results.close()
  pii_results.close()


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
      try:
        change = json.loads(event.data)
      except json.decoder.JSONDecodeError as err:
        print("Error:", err)
        pprint.pprint(event.data)
        continue
      if change['bot']:
        continue
      if change['wiki'] != wiki_filter:
        continue
      if change['namespace'] not in namespaces_filter:
        continue
      if "revision" not in change:
        continue
      if "old" not in change['revision']:
        continue
      callback(change)


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument(
      '--wiki_filter', default='enwiki', help='Wiki to scan, default enwiki.')
  parser.add_argument(
      '--namespaces',
      default='1,3',
      help='Namespaces defined in http://phabricator.wikimedia.'+
      'org/source/mediawiki/browse/master/includes/Defines.php separated by commas.'
  )
  parser.add_argument(
      '--url',
      default='https://stream.wikimedia.org/v2/stream/recentchange',
      help='SSE client url')
  args = parser.parse_args()

  namespaces = set([int(ns) for ns in args.namespaces.split(',')])
  client = sseclient.SSEClient(args.url)

  apikey_data, toxicity, dlp = perspective.get_client()
  def log_change(change):
    return log_event(apikey_data, toxicity, dlp, change)
  watcher(client, args.wiki_filter, namespaces, log_change)
