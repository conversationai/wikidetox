import json
from collections import defaultdict
import datetime
import re
import os

def wikipedia_format_clean(content):
    cleaned_content = '\n'.join([x.strip() for x in content.splitlines() if not(x.strip()) == ''])
    x = 0
    while (len(cleaned_content) >= 2 and cleaned_content[0] == '=' and cleaned_content[-1] == '='):
        cleaned_content = cleaned_content[1:-1]
    while (len(cleaned_content) >= 1 and (cleaned_content[0] == ':' or cleaned_content[0] == '*')):
        cleaned_content = cleaned_content[1:]
    sub_patterns = [('\[EXTERNAL_LINK: .*?\]', 'external_link'), \
                    ('\[REPLYTO: .*?\]', 'replyto'), \
                    ('\[MENTION: .*?\]', 'mention'), \
                    ('\[OUTDENT: .*?\]', ''), \
                    ('\[WIKI_LINK: .*?\]', 'wiki_link')]
    patterns = [('exteral_link', '\[EXTERNAL_LINK: (.*?)\]'), \
                ('replyto_mention', '\[REPLYTO: (.*?)\]'), \
                ('mention', '\[MENTION: (.*?)\]'), \
                ('wiki_link', '\[WIKI_LINK: (.*?)\]')]
    feat = {}
    for feat_name, pa in patterns:
        p = re.compile(pa)
        feat[feat_name] = p.findall(cleaned_content) 
    for p, r in sub_patterns:
        cleaned_content = re.sub(p, r, cleaned_content)
    return cleaned_content

def replyTo_in_conv(conv):
    ret = {}
    for act in conv.values():
        if 'replyTo_id' in act and not(act['replyTo_id'] == None):
           if not(act['replyTo_id'] in conv): act['replyTo_id'] = None
        ret[act['id']] = act
    return ret 

def get_data(constraint):
    good_conversations = defaultdict(dict)
    bad_conversations = defaultdict(dict)
    all_conversations = []
    with open('/scratch/wiki_dumps/matched_conversations/%s_good.json'%(constraint)) as f:
         for line in f:
             cur = json.loads(line)
             cur['timestamp_in_sec'] = (datetime.datetime.strptime(cur['timestamp'], '%Y-%m-%d %H:%M:%S UTC') -datetime.datetime(1970,1,1)).total_seconds() 
             cur['cleaned_content'] = wikipedia_format_clean(cur['content'])
             good_conversations[cur['conversation_id']][cur['id']] = cur
    matches = {}
    with open('/scratch/wiki_dumps/matched_conversations/%s_bad.json'%(constraint)) as f:
         for line in f:
             cur = json.loads(line)
             cur['timestamp_in_sec'] = (datetime.datetime.strptime(cur['timestamp'], '%Y-%m-%d %H:%M:%S UTC') -datetime.datetime(1970,1,1)).total_seconds() 
             cur['cleaned_content'] = wikipedia_format_clean(cur['content'])
             bad_conversations[cur['conversation_id']][cur['id']] = cur
             matches[cur['conversation_id']] = cur['good_conversation_id']
    length = {}
    cnt = 0
    for badid, bad in bad_conversations.items():
        match = matches[badid]
        good = good_conversations[match]
        bad_actions = list(bad.values())
        good_actions = list(good.values())
        bad_end = max([b['timestamp_in_sec'] for b in bad_actions])
        good_end = max([a['timestamp_in_sec'] for a in good_actions])
        bad_actions = [b for b in bad_actions if b['timestamp_in_sec'] < bad_end]
        bad_users = len(set([b['user_text'] for b in bad_actions if 'user_text' in b]))
        good_actions = [b for b in good_actions if b['timestamp_in_sec'] < good_end]
        good_users = len(set([b['user_text'] for b in good_actions if 'user_text' in b]))
        if not(len(bad_actions) == len(good_actions)) or not(bad_users == good_users):
           cnt += 1
           print('Sanity Check Error')
        length[badid] = len(bad_actions)
        length[match] = len(good_actions)
    print(cnt)
    for conversations in [good_conversations, bad_conversations]:
        print(len(list(conversations.keys())))
        for key, val in conversations.items():
            new_val = replyTo_in_conv(val)
            if length[key] <= 10:
               all_conversations.append((key, new_val))
    print(len(all_conversations))
    all_conversations = sorted(all_conversations, key=lambda k: len(k[1].keys()))
    
    os.system('mkdir /scratch/wiki_dumps/%s'%(constraint))
    os.system('mkdir /scratch/wiki_dumps/%s/raw_data'%(constraint))
    for ind, line in enumerate(all_conversations):
        with open('/scratch/wiki_dumps/%s/raw_data/data%d.json'%(constraint, ind%70), 'a') as f:
             f.write(json.dumps(line) +'\n')
    
constraints = ['clean']#['delta2_none', 'delta2_no_users', 'delta3_none', 'delta3_no_users']

#['none', 'attacker_in_conv', 'no_users', 'no_users_attacker_in_conv']    
for c in constraints:
    get_data(c)
    print(c)
    
