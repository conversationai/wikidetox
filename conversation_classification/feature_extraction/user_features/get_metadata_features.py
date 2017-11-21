import json
import pandas as pd
import numpy as np

with open('/scratch/wiki_dumps/user_data/metadata.json') as f:
     usrdata = json.load(f) 

with open('/scratch/wiki_dumps/talk_page_article_link.json') as f:
     subjectpage = json.load(f)

registration = {}
groups = {}
blocking = {}
for user, data in usrdata.items():
    if 'registration' in data and data['registration']:
       registration[user] = timestamp_2_sec(data['registration'])
    if 'groups' in data:
       groups[user] = data['groups']
    else:
       groups[user] = []
    if 'blockedtimestamp' in data:
       blocking[user] = timestamp_2_sec(data['blockedtimestamp'])

constraints = ['delta2_no_users', 'delta2_no_users_attacker_in_conv']
for constraint in constraints:
    with open('/scratch/wiki_dumps/expr_with_matching/%s/data/all.json'%(constraint)) as f:
        for line in f:
            conv_id, clss, conversation = json.loads(line)
            users = []
            user_id = {}
            start_time = np.inf
            for action in conversation['action_feature']:
                start_time = min(start_time, action['timestamp_in_sec']
                if 'user_text' in action:
                    users.append(action['user_text'])      
                    if 'user_id' in action:
                       user_id[action['user_text']] = action['user_id']
                    else:
                       user_id[action['user_text']] = '0|'+ action['user_text']
            for user in users:
                info = {}
                # metadata
                if user in registration: 
                   info['registration'] = registration[user]
                else:
                   info['anon'] = True
                info['groups'] = groups[user]
                if user in blocking and blocking[user] < start_time: 
                   info['blocked'] = blocking[user]
                
                # editing data
                u_id = user_id[user]
                if page_title in subjectpage:  
                   p_id = subjectpage[page_title]            
                else:
                   p_id = -1

  
