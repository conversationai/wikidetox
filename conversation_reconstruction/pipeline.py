from conversation_constructor import Conversation_Constructor
import json
import fileinput
import sys
import os
from multiprocessing import Pool
import time
from pathlib import Path


THERESHOLD = 60 * 30

def reconstruct(input_file):
    with open(input_file, 'r') as f:
         content = json.load(f)
    filename = content['page_id']
    start = time.time()
    w = open('/scratch/wiki_dumps/tmp/%s_conv.json'%(filename), 'w')
    page_history = []
    for rev in content['revisions']:
        rev['page_id'] = content['page_id']
        rev['page_title'] = content['page_title']
        rev['page_namespace'] = content['page_namespace']
        if not('user_text' in rev): rev['user_text'] = None
        if not('user_id' in rev): rev['user_id'] = None
        page_history.append(rev)
    processor = Conversation_Constructor()
    actions_lst = []
    for ind, h in enumerate(page_history):
        actions = processor.process(h, DEBUGGING_MODE = False)
        if time.time() - start > THERESHOLD:
           with open('/scratch/wiki_dumps/long_pages.json', 'a') as log:
                log.write(page_history[0]['page_id'] + '\n')
           w.close()
           os.system('rm /scratch/wiki_dumps/tmp/%s_conv.json'%(filename))
           return 
        for action in actions:
            w.write(json.dumps(action) + '\n')
    w.close()
    os.system('mv /scratch/wiki_dumps/tmp/%s_conv.json /scratch/wiki_dumps/conversations/%s.json'%(filename, filename))
    os.system('rm /scratch/wiki_dumps/tmp/%s.json'%(filename))
    return input_file

pools = []
with open('chunks') as c:
    for line in c:
        pools.append(line[:-1])
print('Data read in %d' % (len(pools)))
p = Pool(70)
result = p.map(reconstruct, pools)
for r in result: 
    print(r.get())
p.close()
p.join()
