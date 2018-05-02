from conversation_display import * 
import json
import fileinput
import sys
import os
from multiprocessing import Pool
import time
from pathlib import Path

def reconstruct(filename):
    actions_lst = []
    actions = {}
    with open('/scratch/wiki_dumps/bq_convs/' + filename, 'r') as f:
         for line in f:
             action = json.loads(line)
             actions_lst.append(action)
             actions[action['id']] = action
    if actions_lst == []:
       return 
    try:
       convs, conv_mapping = group_into_conversations(filename[:-5], actions_lst)
    except:
       return 
    ret  = ''
    for key, val in conv_mapping.items():
        actions[key]['conversation_id'] = val
    for key, val in actions.items():
        ret += json.dumps(val) + '\n'
    number = int(filename[:-5]) % 70
    with open('/scratch/wiki_dumps/conversations%d.json'%(number), 'a') as w:
        w.write(ret)
             

pools = []
with open('/scratch/wiki_dumps/filelist') as c:
    for line in c:
        pools.append(line[:-1])
print('Data read in %d' % (len(pools)))
p = Pool(70)
result = p.map(reconstruct, pools)
p.close()
p.join()
