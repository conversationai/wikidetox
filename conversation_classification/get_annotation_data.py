import json
import pandas as pd

def clean(s):
    ret = s.replace('\t', '[TAB_REPLACEMENT]')
    ret = ret.replace('\n', '[NEWLINE_REPLACEMENT]')
    return ret

maxl = 10
res = []
with open("/scratch/wiki_dumps/len5-11_train.json") as f:
     for line in f:
         conv_id, clss, conversation = json.loads(line)
         actions = sorted(conversation['action_feature'], key=lambda k: (k['timestamp_in_sec'], k['id'].split('.')[1], k['id'].split('.')[2]))
         comments = {}
         cnt = 0
         comment_lst = {} 
         comment_lst['conversation_id'] = conv_id
         for action in actions:          
             if action['comment_type'] == 'COMMENT_ADDING': 
                comment_lst[cnt] = clean(action['content']) + \
                              '\n COMMENTED BY ' + action['user_text'] + '\n COMMENTED AT ' +  \
                                   action['timestamp']
                cnt += 1
                comments[cnt] = action['id']
             if action['comment_type'] == 'SECTION_CREATION': 
                comment_lst[cnt] = clean(action['content']) + \
                              '\n COMMENTED BY ' + action['user_text'] + '\n COMMENTED AT ' +  \
                                   action['timestamp']
                cnt += 1
                comments[cnt] = action['id']
             if action['comment_type'] == 'COMMENT_MODIFICATION':
                if not('parent_id' in action):
                   continue
                for key,val in comments.items():
                    if val == action['parent_id']: 
                       comment_lst[key] = clean(action['content']) + \
                                        '\n COMMENTED BY ' + action['user_text'] + '\n COMMENTED AT ' +  \
                                        action['timestamp']
         res.append(comment_lst)


df = pd.DataFrame(res) 
df.to_csv("/scratch/wiki_dumps/annotations/data.csv", chunksize=5000, encoding = "utf-8", index='False', sep = "\t")
