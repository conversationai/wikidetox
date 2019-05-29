from googleapiclient import discovery
import json

with open("api_key.json") as json_file:
	apikey_data = json.load(json_file)


API_KEY = apikey_data['perspective_key']
# Generates API client object dynamically based on service name and version.
perspective = discovery.build('commentanalyzer', 'v1alpha1', developerKey=API_KEY)
dlp = discovery.build('dlp', 'v2', developerKey=API_KEY)

analyze_request = {
  'comment': { 'text': 'friendly greetings from python' },
  'requestedAttributes': {'TOXICITY': {}}
}

response = perspective.comments().analyze(body=analyze_request).execute()
dlp_request = {
"item":{
"value":"My phone number is (206) 555-0123."
},
"inspectConfig":{
"infoTypes":[
  {
    "name":"PHONE_NUMBER"
  },
  {
    "name":"US_TOLLFREE_PHONE_NUMBER"
  }
],
"minLikelihood":"POSSIBLE",
"limits":{
  "maxFindingsPerItem":0
},
"includeQuote":True
}
}

dlp_response = dlp.projects().content().inspect(body = dlp_request, parent = 'projects/' + apikey_data['project_number']).execute()



##print (json.dumps(response, indent=2))
print (json.dumps(dlp_response, indent=2))