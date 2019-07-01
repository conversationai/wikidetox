""" inputs comments to perspective and dlp apis and detects
toxicity and personal information> has support for csv files,
bigquery tables, and wikipedia talk pages"""
import argparse
import json
import sys
import argparse
import requests
import pandas as pd
import clean
from googleapiclient import errors as google_api_errors
from googleapiclient import discovery
from google.cloud import bigquery


def get_client():
  """ generates API client with personalized API key """
  with open("api_key.json") as json_file:
    apikey_data = json.load(json_file)
  api_key = apikey_data['perspective_key']
  # Generates API client object dynamically based on service name and version.
  perspective = discovery.build('commentanalyzer', 'v1alpha1',
                                developerKey=api_key)
  dlp = discovery.build('dlp', 'v2', developerKey=api_key)
  return (apikey_data, perspective, dlp)


def perspective_request(perspective, comment):
  """ Generates a request to run the toxicity report"""
  analyze_request = {
      'comment':{'text': comment},
      'requestedAttributes': {'TOXICITY': {}, 'THREAT': {}, 'INSULT': {}}
  }
  response = perspective.comments().analyze(body=analyze_request).execute()
  return response

def dlp_request(dlp, apikey_data, comment):
  """ Generates a request to run the cloud dlp report"""
  request_dlp = {
      "item":{
          "value":comment
          },
      "inspectConfig":{
          "infoTypes":[
              {
                  "name":"PHONE_NUMBER"
              },
              {
                  "name":"US_TOLLFREE_PHONE_NUMBER"
              },
              {
                  "name":"DATE_OF_BIRTH"
              },
              {
                  "name":"EMAIL_ADDRESS"
              },
              {
                  "name":"CREDIT_CARD_NUMBER"
              },
              {
                  "name":"IP_ADDRESS"
              },
              {
                  "name":"LOCATION"
              },
              {
                  "name":"PASSPORT"
              },
              {
                  "name":"GCP_CREDENTIALS"
              },
              {
                  "name":"SWIFT_CODE"
              }
              ],
          "minLikelihood":"POSSIBLE",
          "limits":{
              "maxFindingsPerItem":0
              },
          "includeQuote":True
          }
      }
  dlp_response = (dlp.projects().content().inspect(body=request_dlp,
                                                   parent='projects/'+
                                                   apikey_data['project_number']
                                                   ).execute())
  return dlp_response


def contains_pii(dlp_response):
  """ Checking/returning comments that are likely or very likely to contain PII

      Args:
      passes in the resukts from the cloud DLP
      """
  has_pii = False
  if 'findings' not in dlp_response['result']:
    return False, None
  for finding in dlp_response['result']['findings']:
    if finding['likelihood'] in ('LIKELY', 'VERY_LIKELY'):
      has_pii = True
      return (has_pii, finding['infoType']["name"])
  return False, None


def contains_toxicity(perspective_response):
  """Checking/returning comments with a toxicity value of over 50 percent."""
  is_toxic = False
  if (perspective_response['attributeScores']['TOXICITY']['summaryScore']
      ['value'] >= .5):
    is_toxic = True
  return is_toxic

def contains_threat(perspective_response):
  """Checking/returning comments with a toxicity value of over 50 percent."""
  is_threat = False
  if (perspective_response['attributeScores']['THREAT']['summaryScore']
      ['value'] >= .5):
    is_threat = True
  return is_threat

def contains_insult(perspective_response):
  """Checking/returning comments with a toxicity value of over 50 percent."""
  is_insult = False
  if (perspective_response['attributeScores']['INSULT']['summaryScore']
      ['value'] >= .5):
    is_insult = True
  return is_insult


def get_wikipage(pagename):
  """ Gets all content from a wikipedia page and turns it into plain text. """
  # pylint: disable=fixme, line-too-long
  page = ("https://en.wikipedia.org/w/api.php?action=query&prop=revisions&rvprop=content&format=json&formatversion=2&titles="+(pagename))
  get_page = requests.get(page)
  response = json.loads(get_page.content)
  text_response = response['query']['pages'][0]['revisions'][0]['content']
  return text_response

def wiki_clean(get_wikipage):
  text = clean.content_clean(get_wikipage)
  print (text)
  return text

def use_query(content, sql_query, big_q):
  """make big query api request"""
  query_job = big_q.query(sql_query)
  rows = query_job.result()
  strlst = []
  for row in rows:
    strlst.append(str(row[content]))
  return strlst


# pylint: disable=fixme, too-many-locals
def main(argv):
  """ runs dlp and perspective on content passed in """
  parser = argparse.ArgumentParser(description='Process some integers.')
  parser.add_argument('--input_file', help='Location of file to process')
  parser.add_argument('--api_key', help='Location of perspective api key')
  # pylint: disable=fixme, line-too-long
  parser.add_argument('--sql_query', help='choose specifications for query search')
  parser.add_argument('--csv_file', help='choose CSV file to process')
  parser.add_argument('--wiki_pagename', help='insert the talk page name')
  parser.add_argument('--content', help='specify a column in dataset to retreive data from')
  args = parser.parse_args(argv)

  apikey_data, perspective, dlp = get_client()
  pii_results = open("pii_results.txt", "w+")
  toxicity_results = open("toxicity_results.txt", "w+")

  if args.wiki_pagename:
    wiki_response = get_wikipage(args.wiki_pagename)
    wikitext = wiki_clean(wiki_response)
    text = wikitext.split("\n")
  if args.csv_file:
    text = pd.read_csv(args.csv_file)
  if args.sql_query:
    big_q = bigquery.Client.from_service_account_json('querykey.json')
    text = use_query(args.content, args.sql_query, big_q)

  for line in text.comment_text:
    if not line:
      continue
    dlp_response = dlp_request(dlp, apikey_data, line)
    try:
      perspective_response = perspective_request(perspective, line)
    # Perspective can't handle language errors at this time
    except google_api_errors.HttpError as err:
      print("Error:", err)
    has_pii_bool, pii_type = contains_pii(dlp_response)
    if has_pii_bool:
      print(json.dumps({"comment_text":line, "contains_pii": True, "pii_type":pii_type})+"\n")

    if contains_toxicity(perspective_response):
      print(json.dumps({"comment_text":line, "contains_toxicity": True,
        "summaryScore":perspective_response['attributeScores']
                                 ['TOXICITY']['summaryScore']['value']})+"\n")

    if contains_threat(perspective_response):
      print(json.dumps({"comment_text":line, "contains_threat": True,
        "summaryScore":perspective_response['attributeScores']
                                 ['THREAT']['summaryScore']['value']})+"\n")
    if contains_insult(perspective_response):
      print(json.dumps({"comment_text":line, "contains_insult": True,
        "summaryScore":perspective_response['attributeScores']['INSULT']['summaryScore']
      ['value']})+"\n")
      #print(perspective_response)

  toxicity_results.close()
  pii_results.close()
    # print('dlp result:', json.dumps(dlp_response, indent=2))
    # print ("contains_toxicity:", json.dumps(perspective_response, indent=2))


if __name__ == '__main__':
  main(sys.argv[1:])
 

