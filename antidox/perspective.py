import pandas as pd
from googleapiclient import discovery
import argparse
import json
import os
import sys
global perspective
global dlp


def get_client(api_key_filename):
  with open(api_key_filename) as json_file:
    apikey_data = json.load(json_file)
  API_KEY = apikey_data['perspective_key']

  # Generates API client object dynamically based on service name and version.
  perspective = discovery.build(
      'commentanalyzer', 'v1alpha1', developerKey=API_KEY)
  dlp = discovery.build('dlp', 'v2', developerKey=API_KEY)
  return (apikey_data, perspective, dlp)


def perspective_request(perspective, comment):
  analyze_request = {
      'comment': {
          'text': comment
      },
      'requestedAttributes': {
          'TOXICITY': {},
          'THREAT': {},
          'INSULT': {}
      }
  }
  response = perspective.comments().analyze(body=analyze_request).execute()
  return response


def dlp_request(dlp, apikey_data, comment):
  dlp_request = {
      'item': {
          'value': comment
      },
      'inspectConfig': {
          'infoTypes': [{
              'name': 'PHONE_NUMBER'
          }, {
              'name': 'US_TOLLFREE_PHONE_NUMBER'
          }, {
              'name': 'DATE_OF_BIRTH'
          }, {
              'name': 'EMAIL_ADDRESS'
          }, {
              'name': 'CREDIT_CARD_NUMBER'
          }, {
              'name': 'IP_ADDRESS'
          }, {
              'name': 'LOCATION'
          }, {
              'name': 'PASSPORT'
          }, {
              'name': 'PERSON_NAME'
          }, {
              'name': 'ALL_BASIC'
          }],
          'minLikelihood': 'POSSIBLE',
          'limits': {
              'maxFindingsPerItem': 0
          },
          'includeQuote': True
      }
  }
  dlp_response = (
      dlp.projects().content().inspect(
          body=dlp_request,
          parent='projects/' + apikey_data['project_number']).execute())
  return dlp_response


# Checking/returning comments that are likely or very likely to contain PII
def contains_pii(dlp_response):
  has_pii = False
  if 'findings' not in dlp_response['result']:
    return False
  for finding in dlp_response['result']['findings']:
    print('finding:', finding['infoType'], finding['likelihood'])
    if finding['likelihood'] in ('LIKELY', 'VERY_LIKELY'):
      has_pii = True
  return has_pii


# Checking/returning comments with a toxicity value of over 50 percent.
def contains_toxicity(perspective_response):  #has_pii
  is_toxic = False
  if (perspective_response['attributeScores']['TOXICITY']['summaryScore']
      ['value'] >= .5):
    is_toxic = True
  return is_toxic


def main(argv):
  parser = argparse.ArgumentParser()
  parser.add_argument('--input_file', help='Location of file to process')
  parser.add_argument('--api_key', help='Location of perspective api key')
  args = parser.parse_args(argv)

  dataframe = pd.read_csv(args.input_file)
  apikey_data, perspective, dlp = get_client(args.api_key)

  for comment in dataframe.comment_text:
    dlp_response = dlp_request(dlp, apikey_data, comment)
    perspective_response = perspective_request(perspective, comment)
    print('contains pii?', contains_pii(dlp_response))
    print('contains TOXICITY?:', contains_toxicity(perspective_response))
    print(perspective_response['attributeScores']['TOXICITY']['summaryScore']
          ['value'])
    print('=================================================================')

    #print('dlp result:', json.dumps(dlp_response, indent=2))
    #print ("contains_toxicity:", json.dumps(perspective_response, indent=2))


if __name__ == '__main__':
  main(sys.argv[1:])
