from googleapiclient import discovery
import json

with open("api_key.json") as json_file:
	apikey_data = json.load(json_file)

API_KEY = apikey_data['perspective_key']
# Generates API client object dynamically based on service name and version.
perspective = discovery.build('commentanalyzer', 'v1alpha1', developerKey=API_KEY)

analyze_request = {
  'comment': { 'text': 'friendly greetings from python' },
  'requestedAttributes': {'TOXICITY': {}}
}

response = perspective.comments().analyze(body=analyze_request).execute()

import json
print (json.dumps(response, indent=2))