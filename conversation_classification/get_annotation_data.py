import json
import pandas as pd
import hashlib
import itertools
import csv

def clean(s):
    ret = s.replace('\t', ' ')
    ret = ret.replace('\n', ' ')
    while (len(ret) >= 2 and ret[0] == '=' and ret[-1] == '='):
        ret = ret[1:-1]
    while (len(ret) >= 1 and (ret[0] == ':' or ret[0] == '*')):
        ret = ret[1:]

    return ret

def update(snapshot, action):
    Found = False
    if not('user_text' in action):
       action['user_text'] = 'NO_USERTEXT'
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
                act['user_text'] = action['user_text']
                act['timestamp'] = action['timestamp']
                act['page_title'] = action['page_title']
 
                act['parent_ids'] = pids
                act['status'] = 'content changed'
                status = 'content changed'
                act['relative_replyTo'] = -1
                act['absolute_replyTo'] = -1
                act['parent_ids'][action['id']] = True
                for ind, a in enumerate(snapshot):
                    if a['id'] == action['replyTo_id']:
                        act['relative_replyTo'] = ind
                        act['absolute_replyTo'] = a['id']
                snapshot[i] = act
                Found = True
        if not(found):
            act = {}
            act['content'] = clean(action['content'])
            act['id'] = action['id']
            act['indentation'] = action['indentation']
            act['comment_type'] = 'COMMENT_ADDING' #action['comment_type']
            act['toxicity_score'] = action['score']
            act['user_text'] = action['user_text']
            act['timestamp'] = action['timestamp']
            act['absolute_replyTo'] = -1
            act['page_title'] = action['page_title']

            
            act['status'] = 'just added'
            status = 'just added'
            act['relative_replyTo'] = -1
            for ind, a in enumerate(snapshot):
                if 'replyTo_id' in action and a['id'] == action['replyTo_id']:
                    act['relative_replyTo'] = ind
                    act['absolute_replyTo'] = a['id']
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
        act['user_text'] = action['user_text']
        act['timestamp'] = action['timestamp']
        act['page_title'] = action['page_title']
        
        act['absolute_replyTo'] = -1
        act['status'] = 'just added'
        status = 'just added'
        act['relative_replyTo'] = -1
        Found = True
        for ind, a in enumerate(snapshot):
            if 'replyTo_id' in action and a['id'] == action['replyTo_id']:
                act['relative_replyTo'] = ind
                act['absolute_replyTo'] = a['id']
        act['parent_ids'] = {action['id'] : True}
        snapshot.append(act)

    if not(Found): print(action)
    return snapshot, status

def generate_snapshots(conv):
    snapshot = [] # list of (text, user_text, user_id, timestamp, status, replyto, relative_reply_to)
    for action in conv:
        snapshot,status = update(snapshot, action)
    return snapshot

def reformat(act):
    output_dict = {key: act[key] for key in ['id', 'comment_type', 'content', 'timestamp', 'status', 'page_title']}
    output_dict['parent_id'] = parse_absolute_replyTo(act['absolute_replyTo'])
    output_dict['hashed_user_id'] = hashlib.sha1(act['user_text'].encode('utf-8')).hexdigest()
    return output_dict

def parse_absolute_replyTo(value):
    if value == -1:
        return ''
    else:
        return value

def main():
    maxl = None
    res = []
    with open('/scratch/wiki_dumps/attacker_in_conv/len5-11_train.json') as f:
        for i, line in enumerate(f):
            conv_id, clss, conversation = json.loads(line)
            actions = sorted(conversation['action_feature'], key=lambda k: (k['timestamp_in_sec'], k['id'].split('.')[1], k['id'].split('.')[2]))
            # not including the last action
            end_time = max([a['timestamp_in_sec'] for a in actions])
            actions = [a for a in actions if a['timestamp_in_sec'] < end_time]

            snapshot = generate_snapshots(actions)
            for act in snapshot:
                if 'relative_replyTo' in act and not(act['relative_replyTo'] == -1):
                   act['absolute_replyTo'] = snapshot[act['relative_replyTo']]['id']
            ret = {act['id']:reformat(act) for act in snapshot if not(act['status'] == 'removed')}
            res.append(json.dumps(ret))
            if maxl and i > maxl:
                break

    df = pd.DataFrame(res)
    df.columns = ['conversations']
    df.to_csv('/scratch/wiki_dumps/annotations/conversations_as_json_job1.csv', chunksize=5000, encoding = 'utf-8', index=False, quoting=csv.QUOTE_ALL)
    
if __name__ == '__main__':
    main()
