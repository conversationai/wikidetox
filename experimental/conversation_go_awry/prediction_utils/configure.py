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

def configure(constraint):
    UNIGRAMS_FILENAME = "data/bow_features/%s/unigram100.pkl"%(constraint)
    BIGRAMS_FILENAME = "data/bow_features/%s/bigram200.pkl"%(constraint)
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

    attacker_profile_ASPECTS =['proportion_of_being_replied',\
                                 'total_reply_time_gap', 'reply_latency',\
                                'age', 'status', 'number_of_questions_asked', \
				'edits_on_wikipedia_articles']     
    with open('feature_extraction/utils/lexicons') as f:
        LEXICONS = json.load(f)

    with open("feature_extraction/question_features/%s.json"%(constraint)) as f:
        q = json.load(f)
    QUESTIONS = defaultdict(list)
    l = 0
    for key, val in q.items():
        action = key.split('-')[2]
        new_key = key.split('-')[1]
        QUESTIONS[new_key].append({'action_id': action, 'question_type': np.argmin(val['normy_cluster_dist_vector'])})

    with open("data/user_features.json") as f:
         inp = json.load(f)
    user_features = {}
    for conv, users in inp:
        user_features[conv] = users
    ARGS = [STATUS, ASPECTS, attacker_profile_ASPECTS, LEXICONS, QUESTIONS, UNIGRAMS_LIST, BIGRAMS_LIST]
    return user_features, ARGS
