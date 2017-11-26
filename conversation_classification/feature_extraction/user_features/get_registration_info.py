import numpy as np
import pandas as pd
from collections import defaultdict
import os
import datetime
import requests, json
import time
import csv
"""
def load_data(usrlist):
    apilink = 'https://en.wikipedia.org/w/api.php'
    ususers = '|'.join(usrlist) #seperated by '|' #'ususers=' + 
    usprop = 'blockinfo|groups|editcount|registration|emailable|gender' #'usprop=

    #?action=query&list=users&format=json'
    response = requests.get(apilink, 
              params={'action': 'query', 'list': 'users', 'format': 'json', 'ususers': ususers, 'usprop': usprop}) 
    data = response.json()
    return data['query']
"""
users = {}
user_id = {}
constraints = ['delta2_no_users', 'delta2_no_users_attacker_in_conv']
for constraint in constraints:
    with open('/scratch/wiki_dumps/expr_with_matching/%s/data/all.json'%(constraint)) as f:
        for line in f:
            conv_id, clss, conversation = json.loads(line)
            for action in conversation['action_feature']:
                if 'user_text' in action:
                    users[action['user_text']] = []       
                    if 'user_id' in action:
                       user_id[action['user_text']] = action['user_id']
                    else:
                       user_id[action['user_text']] = '0|'+ action['user_text']
"""
usrlist = list(users.keys())
tmp = [usrlist[i:min(i + 8, len(usrlist))] for i in range(0, len(usrlist), 8)]
usrdata = {}
for t in tmp:
    x = load_data(t)
    for user in x['users']:
        usrid = user['name']
        usrdata[usrid] = user
print('data_fetched')
"""
with open('userdata.json') as w:
     usrdata = json.load(w)


registration_dates = [] 
for user, data in usrdata.items():
    if 'registration' in data and data['registration']:
        timestamp_in_sec = (datetime.datetime.strptime(data['registration'], '%Y-%m-%dT%H:%M:%SZ') -datetime.datetime(1970,1,1)).total_seconds()
        registration_dates.append({'user_text': user, 'user_id': user_id[user], 'registration': data['registration'], 'registration_in_sec': timestamp_in_sec})

df = pd.DataFrame(registration_dates)        
df.to_csv('/scratch/wiki_dumps/user_data/metadata.csv', encoding = 'utf-8', index=False, quoting=csv.QUOTE_ALL)


