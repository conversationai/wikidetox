import pandas as pd
from googleapiclient import discovery
import json

with open("api_key.json") as json_file:
	apikey_data = json.load(json_file)

API_KEY = apikey_data['perspective_key']
service = discovery.build('commentanalyzer', 'v1alpha1', developerKey=API_KEY)

dataframe = pd.read_csv("example.csv")
print (dataframe)
print (dataframe.columns)
for comment in dataframe.comment_text:
	print (comment)
	#service = discovery.build('commentanalyzer', 'v1alpha1', developerKey=API_KEY)
	#service = discovery.build('commentanalyzer', 'v1alpha1', developerKey="AIzaSyA5kva-B5eLUBMD-VB426Pan3AlPXzWOXc")
	analyze_request = {
		'comment': { 'text': comment },
		'requestedAttributes': {'TOXICITY': {}, 'THREAT': {}, 'INSULT': {}}
	}
	response = service.comments().analyze(body=analyze_request).execute()
	print (json.dumps(response, indent=2))
	print ("---------------------------------------------------------------------------")