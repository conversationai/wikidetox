import json
import datetime
from collections import defaultdict

conversations = defaultdict(list)
with open('good.json') as f:
     for line in f:
         cur = json.loads(line)
         cur['timestamp_in_sec'] = (datetime.datetime.strptime(cur['timestamp'], '%Y-%m-%d %H:%M:%S UTC') -datetime.datetime(1970,1,1)).total_seconds() 

         conversations[cur['conversation_id']].append(cur)

output = []
for conv, lst in conversations.items():
    lst = sorted(lst, key=lambda k: k['timestamp_in_sec']) 
    ans_lst = []
    cnt = 0
    for ind, item in enumerate(lst):
        if not(ind == 0) and item['timestamp_in_sec'] == lst[ind - 1]['timestamp_in_sec']:
           cnt += 1 
           ans_lst.append(item)
        else:
           if cnt >= int(lst[0]['bad_length']):
              break
           else:
              cnt += 1
              ans_lst.append(item)

    for val in ans_lst:
        output.append(val)

with open('good_filtered.json', 'w') as w:
     for val in output:
         w.write(json.dumps(val) + '\n')
