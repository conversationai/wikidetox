import json
import pandas as pd
import numpy as np
import datetime
import os
from multiprocessing import Pool
import multiprocessing

with open('/scratch/wiki_dumps/user_data/metadata.json') as f:
     usrdata = json.load(f) 

with open('/scratch/wiki_dumps/talk_page_article_link.json') as f:
     subjectpage = json.load(f)

def timestamp_2_sec(timestamp):
    return (datetime.datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%SZ') -datetime.datetime(1970,1,1)).total_seconds()

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

def process(args):
    conv_id, p_id, page_title, users = args
    user_features = {}        
    
    comments = {}
    for user in users:
      #  print(user)
        info = {}
        """
        # metadata
        if user in registration: 
            info['registration'] = registration[user]
        else:
            info['anon'] = True
        info['groups'] = groups[user]
        if user in blocking and blocking[user] < start_time: 
            info['blocked'] = blocking[user]
        
        """
        # editing data
        u_id = user_id[user]
        try:
            with open('/scratch/wiki_dumps/user_data/editing_per_user/%s'%(u_id)) as f:
                edits = pd.read_csv(f)
            info['edits_on_subjectpage'] = len(edits[(edits['page_id'] == p_id) & (edits['timestamp_in_sec'] < start_time)])
            info['edits_on_wikipedia_articles'] = len(edits[edits['timestamp_in_sec'] < start_time])
        except:
            info['edits_on_subjectpage'] = 0
            info['edits_on_wikipedia_articles'] = 0
        """
        week = 7 * 24* 60 * 60
        # talk page data
        try:
            with open('/scratch/wiki_dumps/user_data/talk_per_user/%s'%(user)) as f:
                edits = pd.read_csv(f, sep = '\t')
            edits['timestamp_in_sec'] = edits.apply(lambda x: timestamp_2_sec(x['timestamp']), axis=1)
         #   print(page_title)
            info['edits_on_this_talk_page'] = len(edits[(edits['page_title'] == page_title) & (edits['timestamp_in_sec'] < start_time)])
            info['edits_on_wikipedia_talks'] = len(edits[edits['timestamp_in_sec'] < start_time])               
            comments[user] = edits[edits['timestamp_in_sec'] < start_time - week].sort_values('timestamp_in_sec', ascending=False).head(100)
            comments[user] = comments[user]['comment'].values.tolist()
            comments[user] = [x.replace('NEWLINE', ' ') for x in comments[user]]
            comments[user] = [x.replace('NEWTAB', ' ') for x in comments[user]]
            
        except:
            info['edits_on_this_talk_page'] = 0
            info['edits_on_wikipedia_talks'] = 0
            comments[user] = []
        """
        user_features[user] = info
    name = multiprocessing.current_process().name
    with open('/scratch/wiki_dumps/expr_with_matching/edit_features/%s.json'%(name), 'a') as w:
        w.write(json.dumps([conv_id, user_features]) + '\n')
#    with open('/scratch/wiki_dumps/expr_with_matching/last_comments/%s.json'%(name), 'a') as w:
#        w.write(json.dumps([conv_id, comments]) + '\n')
    print('One Record Written')

constraints = ['delta2_no_users', 'delta2_no_users_attacker_in_conv']
tasks = []
user_id = {}
for constraint in constraints:
    with open('/scratch/wiki_dumps/expr_with_matching/%s/data/all.json'%(constraint)) as f:
        for line in f:
            conv_id, clss, conversation = json.loads(line)
            users = []
            start_time = np.inf
            for action in conversation['action_feature']:
                start_time = min(start_time, action['timestamp_in_sec'])
                if 'user_text' in action:
                    users.append(action['user_text'])      
                    if 'user_id' in action:
                       user_id[action['user_text']] = action['user_id']
                    else:
                       user_id[action['user_text']] = '0|'+ action['user_text']
            page_title = conversation['action_feature'][0]['page_title']
            if page_title in subjectpage:  
                p_id = subjectpage[page_title]            
            else:
                p_id = -1
            page_title = page_title[page_title.find('Talk') + 5:]
            tasks.append((conv_id, p_id, page_title, users))
#['delta2_no_users_attacker_in_conv']
#['delta2_attacker_in_conv', 'delta2_no_users_attacker_in_conv', 'delta3_attacker_in_conv', 'delta3_no_users_attacker_in_conv']

#['none', 'attacker_in_conv', 'no_users', 'no_users_attacker_in_conv']
lst = []
pool = Pool(70) 
os.system('mkdir /scratch/wiki_dumps/expr_with_matching/edit_features') 
#os.system('mkdir /scratch/wiki_dumps/expr_with_matching/last_comments') 
print('Start Processing')
pool.map(process, tasks)

