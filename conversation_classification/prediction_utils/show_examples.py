"""
Copyright 2017 Google Inc.
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""


import re

def clean(s):
    ret = s.replace('\t', ' ')
    ret = ret.replace('\n', ' ')
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
