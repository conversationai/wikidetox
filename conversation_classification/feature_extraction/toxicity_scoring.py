from __future__ import absolute_import
from __future__ import unicode_literals
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import fcntl
import pickle
#from builtins import (
#         bytes, dict, int, list, object, range, str,
#         ascii, chr, hex, input, next, oct, open,
#         pow, round, super,
#         filter, map, zip)


import json
import fileinput
import sys
import os
import multiprocessing
import time
from pathlib import Path
import re

def wikipedia_format_clean(content):
    cleaned_content = '\n'.join([x.strip() for x in content.splitlines() if not(x.strip()) == ''])
    x = 0
    while (len(cleaned_content) >= 2 and cleaned_content[0] == '=' and cleaned_content[-1] == '='):
        cleaned_content = cleaned_content[1:-1]
    while (len(cleaned_content) >= 1 and (cleaned_content[0] == ':' or cleaned_content[0] == '*')):
        cleaned_content = cleaned_content[1:]
    sub_patterns = [('\[EXTERNAL_LINK: .*?\]', 'external_link'), \
                    ('\[REPLYTO: .*?\]', 'replyto'), \
                    ('\[MENTION: .*?\]', 'mention'), \
                    ('\[OUTDENT: .*?\]', ''), \
                    ('\[WIKI_LINK: .*?\]', 'wiki_link')]
    patterns = [('exteral_link', '\[EXTERNAL_LINK: (.*?)\]'), \
                ('replyto_mention', '\[REPLYTO: (.*?)\]'), \
                ('mention', '\[MENTION: (.*?)\]'), \
                ('wiki_link', '\[WIKI_LINK: (.*?)\]')]
    feat = {}
    for feat_name, pa in patterns:
        p = re.compile(pa)
        feat[feat_name] = p.findall(cleaned_content) 
    for p, r in sub_patterns:
        cleaned_content = re.sub(p, r, cleaned_content)
    return cleaned_content, feat

def process(filename):
    actions = []
    with open('/scratch/wiki_dumps/conv_per_page/' + filename, 'r') as f:
         for line in f:
             action = json.loads(line)
             if action['type'] == 'COMMENT_ADDING' or action['type'] == 'SECTION_CREATION' or action['type'] == 'COMMENT_MODIFICATION':
                actions.append(action)
    ret = ''
    
    sid = SentimentIntensityAnalyzer()
    current = multiprocessing.current_process()
    for action in actions:
        # clean out wiki format
        # wiki format feature
        action['clean_content'], wiki_feature = wikipedia_format_clean(action['content'])
        action.update(wiki_feature)

        # collect politeness and bow features
        action['personal_attack'] = clf.predict_proba([action['clean_content']])[0][1]
        with open('/scratch/wiki_dumps/toxicity/%s.json'%(current.name), 'a') as w:
             w.write(json.dumps(action) + '\n')
             

pools = []
clf = pickle.load(open('personal_attack_model'))
with open('/scratch/wiki_dumps/filelist') as c:
    for line in c:
        pools.append(line[:-1])
print('Data read in %d' % (len(pools)))
p = multiprocessing.Pool(70)
result = p.map(process, pools)
p.close()
p.join()
