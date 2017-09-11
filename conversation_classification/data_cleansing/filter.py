import json
from collections import defaultdict
"""
good_conversations = defaultdict(dict)
bad_conversations = defaultdict(dict)
all_conversations = []
with open('good.json') as f:
     for line in f:
         cur = json.loads(line)
         good_conversations[cur['conversation_id']][cur['id']] = cur
with open('bad.json') as f:
     for line in f:
         cur = json.loads(line)
         bad_conversations[cur['conversation_id']][cur['id']] = cur

shouldbe_lst = {}
for conversations in [good_conversations, bad_conversations]:
    print(len(list(conversations.keys())))
    for key, val in conversations.items():
        shouldbe_lst[key] = True
"""
cnta = 0
cntb = 0
with open('/scratch/wiki_dumps/data.json') as f:   
     for line in f:
         conv_id, c = json.loads(line)
         conv= c['action_feature'][0]
         if 'good_conversation_id' in conv:
            look_for = conv['good_conversation_id']
            clss = 0
            cnta += 1
         else:
            look_for = conv['bad_conversation_id']
            cntb += 1
            clss = 1
         with open('/scratch/wiki_dumps/all_data.json', 'a') as w:
            w.write(json.dumps((conv_id, clss, c)) + '\n')  
print(cnta, cntb)
"""
print(len(list(all_processed.keys())))
with open('/scratch/wiki_dumps/all_data.json', 'w') as f:   
    for key, val in all_processed.items():
        f.write(json.dumps((key, val)) + '\n')
"""
"""
all_processed = {}
for ind in range(70):
    with open('/scratch/wiki_dumps/features/data%d.json'%ind) as f:   
         for line in f:
             conv_id, _ = json.loads(line)
             all_processed[conv_id] = true
print('checkpoint')
print(len(list(all_processed.keys())))
for ind in range(70):
    with open('/scratch/wiki_dumps/features/data%d.json'%ind) as f:   
         for line in f:
             _, c = json.loads(line)
             conv = c['action_feature'][0]
             if 'good_conversation_id' in conv:
                look_for = conv['good_conversation_id']
                clss = 0
             else:
                look_for = conv['bad_conversation_id']
                clss = 1
             if look_for in all_processed:
                cur_out = c 
                cur_out['class'] = clss
                with open('/scratch/wiki_dumps/all_data.json', 'a') as w:
                     w.write(json.dumps(cur_out) + '\n')
"""
