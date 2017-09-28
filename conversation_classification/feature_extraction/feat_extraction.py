from __future__ import absolute_import
from __future__ import unicode_literals
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import datetime
from collections import defaultdict
#from builtins import (
#         bytes, dict, int, list, object, range, str,
#         ascii, chr, hex, input, next, oct, open,
#         pow, round, super,
#         filter, map, zip)


import json
import fileinput
import sys
import os
from multiprocessing import Pool
import time
from pathlib import Path
from politeness_with_spacy import politeness_model, request_utils
from constructive.agree import has_agreement, has_disagreement
import re
from spacy.en import English
from constructive.stopwords import stopwords

"""
DEVELOPING NOTES:
- need to read from the raw file ( navigate using id )
"""

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
"""
    conversations = []
    conv = defaultdict(dict)
    with open('/scratch/wiki_dumps/conv_per_page/%s.json'%(filename), 'r') as f:
         for line in f:
             action = json.loads(line)
             if action['id'] in ACTION_LST:
                 conv[action['conversation_id']][action['id']] = action
    for conv_id, actions in conv.items:
        cur = {'id': conv_id, 'actions': actions, 'conversational_features': {}}
        conversations.append(cur)
    ret = ''
""" 

"""
FEATURE EXTRACTION:
in: conversation: conv_id, list of actions
return: featured conversation: dict of {'id': string, 'actions': list of featured actions, 'conversational_features': list of features}
"""
def process(conv_id, actions):
    sid = SentimentIntensityAnalyzer()
    ret_features = {'action_feature' :[]}
    for action_id, action in actions.items():
        _,wiki_feature = wikipedia_format_clean(action['content'])
        action.update(wiki_feature)

        # collect politeness and bow features
        features = politeness_model.score_it(action['cleaned_content'])
        action.update(features)

        # if it is a request
        action['is_request'] = request_utils.check_is_request(action)

        # polarity features
        action['polarity'] = []
        for sent in action['sentences']:
            action['polarity'].append(sid.polarity_scores(sent))

        # lexicon features
        for lexicon_type, lexicon_lst in LEXICONS.items():
            action[lexicon_type] = 0
            for tok in action['unigrams']:
                if tok.lower() in lexicon_lst: 
                    action[lexicon_type] += 1
        action['length'] = len(action['unigrams'])
        
        # agreement and disagreement
        action['has_agree'] = has_agreement([action['cleaned_content']])
        action['has_disagree'] = has_disagreement([action['cleaned_content']])
        
        # stopwords and contentwords
        action['stopwords'] = list(set([tok for tok in action['unigrams'] if tok in stopwords]))
        action['content_words'] = list(set([tok for tok in action['unigrams'] if tok not in stopwords]))
        # pos bigram
       
        action['pos_bigrams'] = [(a, b) for poss in action['pos_tags'] for a, b in zip(poss, poss[1:])]
        actions[action_id] = action
        ret_features['action_feature'].append(action)
        
       
    # reply pair features: 
    conv_feature = {'question_pair': defaultdict(int), 'n_questions': 0, 'stop_adoption': [],\
                    'content_adoption': [], 'pos_adoption': [], 'time_gap': [], \
                    'last_self_stop_repeat': [], 'last_self_content_repeat': [], \
                    'last_self_pos_repeat' : []}
    number_of_responses = {} 
    for action_id, action in actions.items(): 
        number_of_responses[action_id] = 0
    for action_id, action in actions.items(): 
        conv_feature['n_questions'] += int(action['is_request']) 
        if not('replyTo_id' not in action or action['replyTo_id'] == None):
            parent = actions[action['replyTo_id']]
            number_of_responses[parent['id']] += 1
            # question or not
            conv_feature['question_pair'][int(action['is_request']) * 10 + int(parent['is_request'])] += 1
            # stopwords adoption
            stop_repeat = [w for w in action['stopwords'] if w in parent['stopwords']]
            conv_feature['stop_adoption'].append(len(stop_repeat))
            # content word adoption
            content_repeat = [w for w in action['content_words'] if w in parent['content_words']]
            conv_feature['content_adoption'].append(len(content_repeat))
            # pos tag adoption
            pos_repeat = [p for p in action['pos_bigrams'] if p in parent['pos_bigrams']]
            conv_feature['pos_adoption'].append(len(pos_repeat))
            # reply time gap
            conv_feature['time_gap'].append(action['timestamp_in_sec'] - parent['timestamp_in_sec'])

        last_self = None
        if not('user_id' not in action or action['user_id'] == None):
            for aid, act in actions.items():
                if not('user_id' not in act or act['user_id'] == None) and action['user_id'] == act['user_id'] and act['timestamp_in_sec'] < action['timestamp_in_sec']:
                   if last_self == None or last_self['timestamp_in_sec'] < act['timestamp_in_sec']:                               last_self = act
        if last_self == None:
           continue
        # last_self-stopwords repeatition
        stop_repeat = [w for w in action['stopwords'] if w in last_self['stopwords']]
        conv_feature['last_self_stop_repeat'].append(len(stop_repeat))
        # content word adoption
        content_repeat = [w for w in action['content_words'] if w in last_self['content_words']]
        conv_feature['last_self_content_repeat'].append(len(content_repeat))
        # pos tag repeat 
        pos_repeat = [p for p in action['pos_bigrams'] if p in last_self['pos_bigrams']]
        conv_feature['last_self_pos_repeat'].append(len(pos_repeat))
    conv_feature['number_of_responses'] = number_of_responses.values()
    ret_features['conversational_features'] = conv_feature
    return ret_features 
             
def execute(args):
    constraint, number = args
    with open('/scratch/wiki_dumps/expr_with_matching/%s/raw_data/data%d.json'%(constraint, number)) as f:
        for line in f:
            conv_id, conversation = json.loads(line)
            try:
               ret = process(conv_id, conversation)
            except:
               print(conv_id)
               continue
            with open('/scratch/wiki_dumps/expr_with_matching/%s/features/data%d.json'%(constraint, number), 'a') as w:
                 w.write(json.dumps((conv_id, ret))+'\n')

with open('lexicons') as f:
    LEXICONS = json.load(f)
constraints = ['none', 'attacker_in_conv', 'no_users', 'no_users_attacker_in_conv']
lst = []
for c in constraints:
    os.system('mkdir /scratch/wiki_dumps/expr_with_matching/%s/features'%(c)) 
    for i in range(70):
        lst.append((c, i))
pool = Pool(70) 
pool.map(execute, lst)

