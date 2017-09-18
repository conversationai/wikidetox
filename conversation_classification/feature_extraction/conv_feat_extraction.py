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
FEATURE EXTRACTION:
in: conversation: conv_id, list of actions
return: featured conversation: dict of {'id': string, 'actions': list of featured actions, 'conversational_features': list of features}
"""
def process(conv_id, actions):
    ret_features = actions
      
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
             
def execute(number):
    with open('/scratch/wiki_dumps/matched/data%d.json'%number) as f:
        for line in f:
            conv_id, conversation = json.loads(line)
            try:
               ret = process(conv_id, conversation)
            except:
               print(conv_id)
               continue
            with open('/scratch/wiki_dumps/features/data%d.json'%number, 'a') as w:
                 w.write(json.dumps((conv_id, ret))+'\n')

with open('lexicons') as f:
    LEXICONS = json.load(f)
pool = Pool(70) 
pool.map(execute, range(70))

