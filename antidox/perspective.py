import pandas as pd
from googleapiclient import discovery
import json
global perspective
global dlp
import sys


def get_client():
  with open("api_key.json") as json_file:
	  apikey_data = json.load(json_file)
  API_KEY = apikey_data['perspective_key']

  # Generates API client object dynamically based on service name and version.
  perspective = discovery.build('commentanalyzer', 'v1alpha1', developerKey=API_KEY)
  dlp = discovery.build('dlp', 'v2', developerKey=API_KEY)
  return (apikey_data, perspective, dlp)

def perspective_request(perspective, comment):
  analyze_request = {
    'comment': { 'text': comment },
    'requestedAttributes': {'TOXICITY': {}, 'THREAT': {}, 'INSULT': {}}
  }
  response = perspective.comments().analyze(body=analyze_request).execute()
  #print (json.dumps(response, indent=2))
  return response

def dlp_request(dlp, apikey_data, comment):
  dlp_request = {
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
      "name":"GENDER"
    }
  ],
  "minLikelihood":"POSSIBLE",
  "limits":{
    "maxFindingsPerItem":0
  },
  "includeQuote":True
  }
  }
  #if dlp_request["inspectConfig"]["minLikelihood"] == "POSSIBLE" :
  #  print ("this is personal info")
  dlp_response = dlp.projects().content().inspect(body = dlp_request, parent = 'projects/' + apikey_data['project_number']).execute()
  return dlp_response
  #print (json.dumps(dlp_response, indent=2))
  #print (dlp_request.keys())


def contains_pii(dlp_response):
  has_pii = False
  if 'findings' not in dlp_response['result']:
    return False
  for finding in dlp_response['result']['findings']:
    print('finding:', finding['infoType'], finding['likelihood'])
    if finding['likelihood'] in ('LIKELY', 'VERY_LIKELY'):
      has_pii = True
  return has_pii

# def contains_toxicity(perspective_response):
#   if perspective_response['attributeScores']['TOXICITY']['summaryScore']['value'] >= .05

def main(argv):
  dataframe = pd.read_csv("example.csv")
  apikey_data, perspective, dlp = get_client()

  for comment in dataframe.comment_text:
    #print (comment)
    dlp_response = dlp_request(dlp, apikey_data, comment)
    print('dlp result:', json.dumps(dlp_response, indent=2))
    print('contains pii?', contains_pii(dlp_response))
  # print (perspective_response['attributeScores']['TOXICITY']['summaryScore']['value'])

    #perspective_response = perspective_request(perspective, comment)
    # if contains_toxicity(perspective_response):
    #print ("contains_toxicity:", json.dumps(perspective_response, indent=2))
  #print (dlp_response['result'])

if __name__ == '__main__':
  main(sys.argv[1:])

  #results - findings: list of dict - findings - likelihood  