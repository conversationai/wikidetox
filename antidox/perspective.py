""" inputs comments to perspective and dlp apis and detects
toxicity and personal information> has support for csv files,
bigquery tables, and wikipedia talk pages"""
# TODO(tamajongnc): make cleaned_content an argument
# TODO(tamajongnc): make cleaned_content an argument
import argparse
import json
import sys
import pandas as pd
from googleapiclient import discovery
from googleapiclient import errors as google_api_errors
from google.cloud import bigquery



def get_client(api_key_filename):
  """ generates API client with personalized API key """
  with open(api_key_filename) as json_file:
    apikey_data = json.load(json_file)
  api_key = apikey_data['perspective_key']
  # Generates API client object dynamically based on service name and version.
  perspective = discovery.build('commentanalyzer', 'v1alpha1',
                                developerKey=api_key)
  dlp = discovery.build('dlp', 'v2', developerKey=api_key)


  return (apikey_data, perspective, dlp, big_q)


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
                  "name":"PERSON_NAME"
              },
              {
                  "name":"ALL_BASIC"
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
# Checking/returning comments that are likely or very likely to contain PII

def contains_pii(dlp_response):
  """ specifically checks the dlp response for results containing PII"""
  has_pii = False
  if 'findings' not in dlp_response['result']:
    return False, None
  for finding in dlp_response['result']['findings']:
    if finding['likelihood'] in ('LIKELY', 'VERY_LIKELY'):
      # print('finding:', finding['infoType'], finding['likelihood'])
      has_pii = True
      return (has_pii, finding['infoType']["name"])
  return False, None
# Checking/returning comments with a toxicity value of over 50 percent.

def contains_toxicity(perspective_response):
  """ specifically checks the perspective response for toxicity score"""
  is_toxic = False
  if (perspective_response['attributeScores']['TOXICITY']['summaryScore']
      ['value'] >= .5):
    is_toxic = True
  return is_toxic


def use_query(args.content, sql_query):
  """make big query api request"""
  big_q = bigquery.Client.from_service_account_json(querkey.json)
  query_job = client.query(sql_query)
  rows = query_job.result()
  strlst = []
  for row in rows:
    strlst.append(str(row.args.content))
  return strlst

# pylint: disable=fixme, too-many-locals
def main(argv):
  """runs dlp and perspective on content """
  parser = argparse.ArgumentParser(description='Process some integers.')
  parser.add_argument('--input_file', help='Location of file to process')
  parser.add_argument('--api_key', help='Location of perspective api key')
  parser.add_argument('--sql_query', help= 'choose specifications for query search')
  parser.add_argument('--csv_file', help= 'input csv file')
  parser.add_argument('--content', help= 'specify a column in dataset to retreive data from')
  args = parser.parse_args(argv)
  apikey_data, perspective, dlp, big_q = get_client('api_key.json', 'querykey.json')
  if args.csv_file:
    text = pd.read_csv(args.csv_file)
  if args.sql_query:
    text = use_query(args.content, args.sql_query)
  pii_results = open("pii_results.txt", "w+")
  toxicity_results = open("toxicity_results.txt", "w+")


  for line in text:
    try:
      print(line)
      print('==============================================\n')
      dlp_response = dlp_request(dlp, apikey_data, line)
      perspective_response = perspective_request(perspective, line)
      has_pii_bool, pii_type = contains_pii(dlp_response)
      if has_pii_bool:
        pii_results.write(str(line)+"\n"+'contains pii?'+"Yes"+"\n"
                          +str(pii_type)+"\n"
                          +"==============================================="+"\n")
      if contains_toxicity(perspective_response):
        toxicity_results.write(str(line)+"\n" +"contains TOXICITY?:"+
                               "Yes"+"\n"+
                               str(perspective_response['attributeScores']
                                   ['TOXICITY']['summaryScore']['value'])+"\n"
                               +"=========================================="+"\n")
    except google_api_errors.HttpError as err:
      print('error', err)
  toxicity_results.close()
  pii_results.close()
    # print('dlp result:', json.dumps(dlp_response, indent=2))
    # print ("contains_toxicity:", json.dumps(perspective_response, indent=2))
if __name__ == '__main__':
  main(sys.argv[1:])
