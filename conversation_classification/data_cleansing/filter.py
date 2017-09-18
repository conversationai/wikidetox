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
lst = []
with open('/scratch/wiki_dumps/train_test/all.json') as f:   
     for line in f:
         conv_id, clss, c = json.loads(line)
         conv= c['action_feature'][0]
         t1 = min([a['timestamp_in_sec'] for a in c['action_feature']])
         t2 = max([a['timestamp_in_sec'] for a in c['action_feature']])
         if t2 == t1:
            lst.append(conv['bad_conversation_id'])
            lst.append(conv_id)
print(len(lst))
with open('/scratch/wiki_dumps/all_data.json', 'w') as w:
    with open('/scratch/wiki_dumps/train_test/all.json') as f:   
        for line in f:
            conv_id, clss, c = json.loads(line)
            if not(conv_id in lst):
               w.write(json.dumps((conv_id, clss, c)) + '\n')  
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
