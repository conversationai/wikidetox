import json
from collections import defaultdict
import datetime
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
    return cleaned_content


good_conversations = defaultdict(dict)
bad_conversations = defaultdict(dict)
all_conversations = []
with open('good.json') as f:
     for line in f:
         cur = json.loads(line)
         cur['timestamp_in_sec'] = (datetime.datetime.strptime(cur['timestamp'], '%Y-%m-%d %H:%M:%S UTC') -datetime.datetime(1970,1,1)).total_seconds() 
         cur['cleaned_content'] = wikipedia_format_clean(cur['content'])
         good_conversations[cur['conversation_id']][cur['id']] = cur
with open('bad.json') as f:
     for line in f:
         cur = json.loads(line)
         cur['timestamp_in_sec'] = (datetime.datetime.strptime(cur['timestamp'], '%Y-%m-%d %H:%M:%S UTC') -datetime.datetime(1970,1,1)).total_seconds() 
         cur['cleaned_content'] = wikipedia_format_clean(cur['content'])
         bad_conversations[cur['conversation_id']][cur['id']] = cur
for conversations in [good_conversations, bad_conversations]:
    print(len(list(conversations.keys())))
    for key, val in conversations.items():
        all_conversations.append((key, val))
print(len(all_conversations))
all_conversations = sorted(all_conversations, key=lambda k: len(k[1].keys()))
should_be_lst = all_conversations.keys()
"""
for ind, line in enumerate(all_conversations):
    with open('/scratch/wiki_dumps/matched/data%d.json'%(ind%70), 'a') as f:
         f.write(json.dumps(line) +'\n')
"""
