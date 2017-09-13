import json
import pandas as pd
from conversation_display import *

def clean(s):
    ret = s.replace('\t', '[TAB_REPLACEMENT]')
    ret = ret.replace('\n', '[NEWLINE_REPLACEMENT]')
    while (len(ret) >= 2 and ret[0] == '=' and ret[-1] == '='):
        ret = ret[1:-1]
    while (len(ret) >= 1 and (ret[0] == ':' or ret[0] == '*')):
        ret = ret[1:]

    return ret

def update(snapshot, action):
    Found = False
    if action['comment_type'] == 'COMMENT_REMOVAL':
        for ind, act in enumerate(snapshot):
            if 'parent_id' in action and action['parent_id'] in act['parent_ids']:
                act['status'] = 'removed'
                status = 'removed'
                snapshot[ind] = act
                Found = True
    if action['comment_type'] == 'COMMENT_RESTORATION':
        for ind, act in enumerate(snapshot):
            if 'parent_id' in action and action['parent_id'] in act['parent_ids']:
                act['status'] = 'restored'
                act['content'] = action['content']
                status = 'restored'
                snapshot[ind] = act
                Found = True
    if action['comment_type'] == 'COMMENT_MODIFICATION':
        found = False
        for i, act in enumerate(snapshot):
            if 'parent_id' in action and action['parent_id'] in act['parent_ids']:
                found = True
                pids = act['parent_ids']
                act = {}
                act['content'] = clean(action['content'])
                act['id'] = action['id']
                act['indentation'] = action['indentation']
                act['comment_type'] = action['comment_type']
                act['toxicity_score'] = action['score']
 
                act['parent_ids'] = pids
                act['status'] = 'content changed'
                status = 'content changed'
                act['relative_replyTo'] = -1
                act['parent_ids'][action['id']] = True
                for ind, a in enumerate(snapshot):
                    if a['id'] == action['replyTo_id']:
                        act['relative_replyTo'] = ind
                snapshot[i] = act
                Found = True
        if not(found):
            act = {}
            act['content'] = clean(action['content'])
            act['id'] = action['id']
            act['indentation'] = action['indentation']
            act['comment_type'] = action['comment_type']
            act['toxicity_score'] = action['score']
            
            act['status'] = 'just added'
            status = 'just added'
            act['relative_replyTo'] = -1
            for ind, a in enumerate(snapshot):
                if 'replyTo_id' in action and a['id'] == action['replyTo_id']:
                    act['relative_replyTo'] = ind
            act['parent_ids'] = {action['id'] : True}
            snapshot.append(act)
            Found = True
    if action['comment_type'] == 'COMMENT_ADDING' or action['comment_type'] == 'SECTION_CREATION':
        act = {}
        act['content'] = clean(action['content'])
        act['id'] = action['id']
        act['indentation'] = action['indentation']
        act['comment_type'] = action['comment_type']
        act['toxicity_score'] = action['score']

        act['status'] = 'just added'
        status = 'just added'
        act['relative_replyTo'] = -1
        Found = True
        for ind, a in enumerate(snapshot):
            if 'replyTo_id' in action and a['id'] == action['replyTo_id']:
                act['relative_replyTo'] = ind
        act['parent_ids'] = {action['id'] : True}
        snapshot.append(act)

    if not(Found): print(action)
    return snapshot, status


def generate_snapshots(conv):
    snapshot = [] # list of (text, user_text, user_id, timestamp, status, replyto, relative_reply_to)
    for action in conv:
        snapshot,status = update(snapshot, action)
    return snapshot

maxl = 10
res = []
with open("/scratch/wiki_dumps/train_test/len5-11_train.json") as f:
     for line in f:
         conv_id, clss, conversation = json.loads(line)
         actions = sorted(conversation['action_feature'], key=lambda k: (k['timestamp_in_sec'], k['id'].split('.')[1], k['id'].split('.')[2]))
         snapshot = generate_snapshots(actions)
         ret = {ind:json.dumps(s) for ind, s in enumerate(snapshot) if not(s['status'] == 'removed')}
         res.append(ret)


df = pd.DataFrame(res) 
df.to_csv("/scratch/wiki_dumps/annotations/data.csv", chunksize=5000, encoding = "utf-8", index='False', sep = "\t")
