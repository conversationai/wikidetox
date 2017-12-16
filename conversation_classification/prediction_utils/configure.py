"""
Copyright 2017 Google Inc.
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""


import json
import pickle as cPickle
import numpy as np
from collections import defaultdict

def configure(constraint, suffix):
    UNIGRAMS_FILENAME = "/scratch/wiki_dumps/paired_conversations/%s/bow_features/unigram100%s.pkl"%(constraint, suffix)
    BIGRAMS_FILENAME = "/scratch/wiki_dumps/paired_conversations/%s/bow_features/bigram200%s.pkl"%(constraint, suffix)
    UNIGRAMS_LIST = cPickle.load(open(UNIGRAMS_FILENAME, "rb"))
    BIGRAMS_LIST = cPickle.load(open(BIGRAMS_FILENAME, "rb"))

    STATUS = {4: ['founder', 'sysop'], 
      3: ['accountcreator', 'bureaucrat', 'checkuser'], \
      2: [ 'abusefilter', 'abusefilter-helper', 'autoreviewer', 'extendedmover',  \
        'filemover', 'import', 'oversight', 'patroller', \
        'reviewer','rollbacker','templateeditor','epadmin', 'epcampus', 'epcoordinator',\
        'epinstructor', 'eponline'],\
      1: ['massmessage-sender', 'ipblock-exempt', 'extendedconfirmed',\
            'autoconfirmed', 'researcher', 'user']}
    ASPECTS = ['age', 'status', 'comments_on_same_talk_page', 'comments_on_all_talk_pages',\
        'edits_on_subjectpage', 'edits_on_wikipedia_articles', 'history_toxicity']

    attacker_profile_ASPECTS = ['proportion_of_being_replied',\
            'proportion_of_utterance_over_all', 'total_length_of_utterance', \
            'maximum_toxicity', 'age', 'status', 'comments_on_all_talk_pages',\
            'edits_on_wikipedia_articles', 'history_toxicity', \
            'self_modification', 'other_modification', 'pron_you_usage', \
            'gratitude_usage', 'max_negativity']
    with open('feature_extraction/utils/lexicons') as f:
        LEXICONS = json.load(f)

    with open("feature_extraction/question_features/%s.json"%(constraint)) as f:
        q = json.load(f)
    QUESTIONS = defaultdict(list)
    l = 0
    for key, val in q.items():
        action = key.split('-')[2]
        new_key = key.split('-')[1]
        QUESTIONS[new_key].append(np.argmin(val['normy_cluster_dist_vector'])) 

    with open("/scratch/wiki_dumps/paired_conversations/user_features/all.json") as f:
         inp = json.load(f)
    user_features = {}
    for conv, users in inp:
        user_features[conv] = users
    ARGS = [STATUS, ASPECTS, attacker_profile_ASPECTS, LEXICONS, QUESTIONS, UNIGRAMS_LIST, BIGRAMS_LIST]
    return user_features, ARGS
