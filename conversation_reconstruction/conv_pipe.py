from conversation_display import * 
import json
import fileinput
import sys
import os
from multiprocessing import Pool
import time
from pathlib import Path

def reconstruct(number):
    actions_lst = []
    actions = {}
    with open('/scratch/wiki_dumps/updated/conversations%d.json'%number, 'r') as f:
         for line in f:
             action = json.loads(line)
             actions_lst.append(action)
             actions[action['id']] = action
    if actions_lst == []:
       return 
    conv_mapping = {}
    actions_lst = sorted(actions_lst, key = lambda k : (int(k['rev_id']), int(k['indentation'])))

    inspect = '67065595.3923.3923'
    for action in actions_lst:
  
        if action['id'] == inspect or action['replyTo_id'] == inspect:
           print(action['id'], action['replyTo_id'], action['conversation_id'])
           print(action)
        continue
"""
        try:
           if action['type'] == 'COMMENT_REARRANGEMENT':
              continue
           if action['type'] == 'COMMENT_ADDING' or action['type'] == 'COMMENT_MODIFICATION' \
              or action['type'] == 'SECTION_CREATION':
              if action['replyTo_id'] == None:
                 action['conversation_id'] = action['id']
              else:
                 if action['id'] == action['replyTo_id']:
                    action['conversation_id'] = action['id']
                 else:
                    action['conversation_id'] = conv_mapping[action['replyTo_id']]
           else:
              if action['id'] == action['parent_id']:
                 action['conversation_id'] = action['id']
              else:
                 action['conversation_id'] = conv_mapping[action['parent_id']]
        except:
           print(action)

        conv_mapping[action['id']] = action['conversation_id']
        with open('/scratch/wiki_dumps/updated/conversations%d.json'%(number), 'a') as w:
           w.write(json.dumps(action) + '\n')
        if (action['type'] == 'COMMENT_ADDING' or action['type'] == 'COMMENT_MODIFICATION' \
              or action['type'] == 'SECTION_CREATION') and not(action['replyTo_id'] == None):
           assert(action['conversation_id'] == conv_mapping[action['replyTo_id']])
        if action['id'] == '145600288.20051.20063' or action['replyTo_id'] == '145600288.20051.20063':
           print(action['id'], action['replyTo_id'], action['conversation_id'])
"""

p = Pool(70)
result = p.map(reconstruct, range(70))
p.close()
p.join()
