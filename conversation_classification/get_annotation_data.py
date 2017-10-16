import json
import pandas as pd
import hashlib
import itertools
import csv
import re
import os

def clean(s):
    ret = s.replace('\t', ' ')
    ret = ret.replace('\n', ' ')
#    while (len(ret) >= 2 and ret[0] == '=' and ret[-1] == '='):
#        ret = ret[1:-1]
    while (len(ret) >= 1 and (ret[0] == ':' or ret[0] == '*')):
        ret = ret[1:]
    sub_patterns = [('EXTERNAL_LINK: ', ''), \
                    ('\[REPLYTO: .*?\]', ''), \
                    ('\[MENTION: .*?\]', ''), \
                    ('\[OUTDENT: .*?\]', ''), \
                    ('WIKI_LINK: ', '')]
    for p, r in sub_patterns:
        ret = re.sub(p, r, ret)


    return ret

def update(snapshot, action):
    Found = False
    if not('user_text' in action):
       action['user_text'] = 'Anonymous'
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
                act['content'] = clean(action['content'])
                act['timestamp_in_sec'] = action['timestamp_in_sec']
                status = 'restored'
                snapshot[ind] = act
                Found = True
    if action['comment_type'] == 'COMMENT_MODIFICATION':
        found = False
        for i, act in enumerate(snapshot):
            if 'parent_id' in action and action['parent_id'] in act['parent_ids']:
                found = True
                pids = act['parent_ids']
                new_act = {}
                new_act['content'] = clean(action['content'])
                new_act['id'] = action['id']
                new_act['indentation'] = action['indentation']
                new_act['comment_type'] = action['comment_type']
                new_act['toxicity_score'] = action['score']
                if 'bot' in action['user_text'].lower(): 
                   new_act['user_text'] = act['user_text']
                else:
                   new_act['user_text'] = action['user_text']
                new_act['timestamp'] = action['timestamp']
                new_act['timestamp_in_sec'] = action['timestamp_in_sec']
                new_act['page_title'] = action['page_title']
 
                new_act['parent_ids'] = pids
                new_act['status'] = 'content changed'
                status = 'content changed'
                new_act['relative_replyTo'] = -1
                new_act['absolute_replyTo'] = -1
                new_act['parent_ids'][action['id']] = True
                for ind, a in enumerate(snapshot):
                    if action['replyTo_id'] in a['parent_ids']:
                        new_act['relative_replyTo'] = ind
                        new_act['absolute_replyTo'] = a['id']
                snapshot[i] = new_act
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
            act['timestamp_in_sec'] = action['timestamp_in_sec']
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
        act['timestamp_in_sec'] = action['timestamp_in_sec']
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
    output_dict = {key: act[key] for key in ['id', 'comment_type', 'content', 'timestamp', 'status', 'page_title', 'user_text']}
    output_dict['parent_id'] = parse_absolute_replyTo(act['absolute_replyTo'])
#    output_dict['hashed_user_id'] = hashlib.sha1(act['user_text'].encode('utf-8')).hexdigest()
    return output_dict

def parse_absolute_replyTo(value):
    if value == -1:
        return ''
    else:
        return value

def main(constraint, job):
    maxl = None
    res = []
    max_len = 0
    path = '/scratch/wiki_dumps/expr_with_matching/' + constraint  + '/data'
    os.system('cat %s/develop.json %s/train.json %s/develop.json > %s/all.json'%(path, path, path, path))
    cnt = 0
    with open('annotated.json') as w:
         annotated = json.load(w) 
    with open('annotated_2.json') as w:
         accepted = json.load(w) 

    if job == 2:
        accepted = []
    if job == 1:
        with open('%s_conversations_with_reasonable_length.json'%(constraint)) as w:
           accepted = json.load(w) 
    if job == 3:
       annotated = annotated + accepted



    with open('/scratch/wiki_dumps/expr_with_matching/%s/data/all.json'%(constraint)) as f:
        for i, line in enumerate(f):
            conv_id, clss, conversation = json.loads(line)
            if job < 3:
               if conv_id in annotated:
                  continue
            else:
               if not(conv_id in annotated):
                  continue
            if job == 1:
               if not(conv_id in accepted):
                  continue
            actions = sorted(conversation['action_feature'], key=lambda k: (k['timestamp_in_sec'], k['id'].split('.')[1], k['id'].split('.')[2]))

            # not including the last action
            end_time = max([a['timestamp_in_sec'] for a in actions])
            if job == 1:
               actions = [a for a in actions if a['timestamp_in_sec'] < end_time]
            

            snapshot = generate_snapshots(actions)
            last_comment = None
            for ind, act in enumerate(snapshot):
                if 'relative_replyTo' in act and not(act['relative_replyTo'] == -1)\
                   and not(act['relative_replyTo'] == ind):
                     act['absolute_replyTo'] = snapshot[act['relative_replyTo']]['id']
                if act['timestamp_in_sec'] == end_time:
                     father = ind
                     depth = -1
                     while father:
                         depth += 1
                         if 'relative_replyTo' in snapshot[father] \
                            and not(snapshot[father]['relative_replyTo'] == -1)\
                            and not(snapshot[father]['relative_replyTo'] == father):
                                father = snapshot[father]['relative_replyTo']
                         else:
                            break
                         if depth > 10:
                            depth = -1
                            break
                     if depth == -1:
                        continue
                     if last_comment == None or depth > last_comment['depth']:
                        last_comment = act
                        last_comment['depth'] = depth

                snapshot[ind] = act
            if job == 3:  
               if not(last_comment == None):
                  res.append({'id': conv_id, 'comment': last_comment})
               continue
            
            ret = {act['id']:reformat(act) for act in snapshot if not(act['status'] == 'removed')}
            length = len(ret.keys())

            if job == 2:
                if length > 10:
                   cnt += 1
                else:
                   accepted.append(conv_id)
                   res.append(json.dumps(ret))
            else:
               res.append(json.dumps(ret))
            max_len = max(max_len, length) 
            if maxl and i > maxl:
                break
    if job == 2:
       with open('%s_conversations_with_reasonable_length.json'%constraint, 'w') as w:
          json.dump(accepted, w)


    df = pd.DataFrame(res)
    if job < 3:
       df.columns = ['conversations']
    else:
       return df
    #conversations_as_json_job1.csv
    os.system('mkdir /scratch/wiki_dumps/expr_with_matching/%s/annotations'%(constraint))
    df.to_csv('/scratch/wiki_dumps/expr_with_matching/%s/annotations/conversations_as_json_job%d.csv'%(constraint, job), chunksize=5000, encoding = 'utf-8', index=False, quoting=csv.QUOTE_ALL)
   
if __name__ == '__main__':
    constraints = ['delta2_no_users', 'delta2_no_users_attacker_in_conv']
    df = []
    for c in constraints:
#        main(c, 2) 
#        main(c, 1)
        df.append(main(c, 3)) # Only the last comment
        print(c)
    df = pd.concat(df)
    df.to_csv('/scratch/wiki_dumps/expr_with_matching/toxicity_in_context.csv', chunksize=5000, encoding = 'utf-8', index=False, quoting=csv.QUOTE_ALL)
 

