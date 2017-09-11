import json
from collections import defaultdict
import random

good_conversations = defaultdict(dict)
bad_conversations = defaultdict(dict)
all_conversations = []
with open('/scratch/wiki_dumps/matched/good.json') as f:
     for line in f:
         cur = json.loads(line)
         good_conversations[cur['conversation_id']][cur['id']] = cur
with open('/scratch/wiki_dumps/matched/bad.json') as f:
     for line in f:
         cur = json.loads(line)
         bad_conversations[cur['conversation_id']][cur['id']] = cur

shouldbe_lst = {}
for conversations in [good_conversations, bad_conversations]:
    print(len(list(conversations.keys())))
    for key, val in conversations.items():
        shouldbe_lst[key] = True

conv_pairs = defaultdict(list)
conversations = {}
maxl = 0
existed = {}
for ind in range(70):
    with open('/scratch/wiki_dumps/features/data%d.json'%ind) as f:
        for line in f:
            conv_id, conversation = json.loads(line)
            conv= conversation['action_feature'][0]
            if 'good_conversation_id' in conv:
               clss = 0
            else:
               clss = 1
            conversations[conv_id] = (conv_id, clss, conversation)
            if clss == 1:
               if conv_id in existed:
                  continue
               existed[conv_id] = True
               l = int(conversation['action_feature'][0]['bad_length'])
               conv_pairs[l].append((conv_id, conversation['action_feature'][0]['bad_conversation_id']))
               maxl = max(maxl, l)
print(maxl)

# 0~4
for l in range(5):
   for c in conv_pairs[l]: 
       id1, id2 = c
       x = random.random()
       if not(id1 in shouldbe_lst and id2 in shouldbe_lst and id2 in conversations):
          continue
       if x > 0.9:
          with open('/scratch/wiki_dumps/len0-4_test.json', 'a') as f:
               f.write(json.dumps(conversations[id1]) + '\n')
               f.write(json.dumps(conversations[id2]) + '\n')
       else:
          with open('/scratch/wiki_dumps/len0-4_train.json', 'a') as f:
               f.write(json.dumps(conversations[id1]) + '\n')
               f.write(json.dumps(conversations[id2]) + '\n')

             
# 5~10
for l in range(5, 11):
   for c in conv_pairs[l]: 
       id1, id2 = c
       if not(id1 in shouldbe_lst and id2 in shouldbe_lst and id2 in conversations):
          continue
       x = random.random()
       if x > 0.9:
          with open('/scratch/wiki_dumps/len5-11_test.json', 'a') as f:
               f.write(json.dumps(conversations[id1]) + '\n')
               f.write(json.dumps(conversations[id2]) + '\n')
       else:
          with open('/scratch/wiki_dumps/len5-11_train.json', 'a') as f:
               f.write(json.dumps(conversations[id1]) + '\n')
               f.write(json.dumps(conversations[id2]) + '\n')
 
# >10
for l in range(10, maxl+1):
   for c in conv_pairs[l]: 
       id1, id2 = c
       if not(id1 in shouldbe_lst and id2 in shouldbe_lst and id2 in conversations):
          continue
       x = random.random()
       if x > 0.9:
          with open('/scratch/wiki_dumps/len11-_test.json', 'a') as f:
               f.write(json.dumps(conversations[id1]) + '\n')
               f.write(json.dumps(conversations[id2]) + '\n')
       else:
          with open('/scratch/wiki_dumps/len11-_train.json', 'a') as f:
               f.write(json.dumps(conversations[id1]) + '\n')
               f.write(json.dumps(conversations[id2]) + '\n')
 


