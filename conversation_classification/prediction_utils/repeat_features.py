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
from scipy.sparse import csr_matrix
import random
import matplotlib.pyplot as plt
from collections import defaultdict
import math
import re
import copy


def _get_repeatition_features(actions):
    """
        Extracts features that reflect changes in two consecutive utterances A and A' from a single participant:
           - negative_increase: has participant expressing no negative polarity in A, but expressing negative polartiy in A' 
           - positive_decrease: has participant expressing positive polarity in A, but expressing no positive polartiy in A' 
           - toxicity_raise: has participant with toxicity score in A' larger than then toxicity score in A by a margin(0.05 in the code)
           - consecutive_negative: has participant expressing negative polarity in both A and A'
           - negative_decrease: has participant expressing negative polarity in A, but expressing no negative polartiy in A' 
           - positive_increase: has participant expressing no positive polarity in A, but expressing positive polartiy in A'  
           - max_toxicity_gap: maximum gap between toxicity score of A and A' among all pairs
           - mean_toxicity_gap: average gap between toxicity score of A and A' among all pairs
           - last_toxicity_gap: the gap between toxicity score between the two last utterances from the last participant
           - max_polarity_gap: maximum change of average polarity score between A and A' among all pairs
           - has_stopwords_repeat: has a participant repeats a stopword in A and A'
           - has_content_words_repeat: has a participant repeats a non-stopword in A and A'
    """
    # Initialize
    unigrams, bigrams = set([]), set([])
    ret = {'negative_increase': 0, 'positive_decrease': 0, 'toxicity_raise': 0, 'consecutive_negative': 0,
          'negative_decrease': 0, 'positive_increase': 0, 'max_toxicity_gap': 0, \
           'mean_toxicity_gap': 0, 'last_toxicity_gap': 0, 'max_polarity_gap': 0}
    self_feat = 0
    for repeat in ['content_words', 'stopwords']:
        ret['has_%s_repeat'%(repeat)] = 0
    total_gaps = 0
    for action in actions:  
        # Find the last utterance by the same participant
        last_self = None
        if not('user_text' not in action or action['user_text'] == None):
            for act in actions:
                if not('user_text' not in act or act['user_text'] == None) and \
                   action['user_text'] == act['user_text'] and \
                   act['timestamp_in_sec'] < action['timestamp_in_sec']:
                    if last_self == None or last_self['timestamp_in_sec'] < act['timestamp_in_sec']:                               
                        last_self = act

        if not(last_self == None):
            # Repetition of words
            for repeat in ['content_words', 'stopwords']:
                cur_repeat = (len(set(action[repeat]) & set(last_self[repeat])) > 0)
                if cur_repeat > 0:
                    ret['has_%s_repeat'%(repeat)] = 1 
            # Change of toxicity score of utterance
            if last_self['score'] < action['score'] - 0.05:
                ret['toxicity_raise'] = 1
            ret['max_toxicity_gap'] = max(ret['max_toxicity_gap'], action['score'] - last_self['score'])
            ret['last_toxicity_gap'] = action['score'] - last_self['score']
            ret['mean_toxicity_gap'] += action['score'] - last_self['score']
            total_gaps += 1
            # Change of polarity of utterance
            last_p = 0
            cur_p = 0
            cur_polarity_score = []
            last_polarity_score = []
            for p in last_self['polarity']: 
                if p['compound'] < -0.5: last_p = 1
                last_polarity_score.append(p['compound'])
            for p in action['polarity']: 
                if p['compound'] < -0.5: cur_p = 1
                cur_polarity_score.append(p['compound'])
            if cur_p > last_p: ret['negative_increase'] = 1
            if cur_p < last_p: ret['negative_decrease'] = 1
            if cur_p == 1 and last_p == 1: ret['consecutive_negative'] = 1
            ret['max_polarity_gap'] = max(ret['max_polarity_gap'], \
                                          np.mean(cur_polarity_score) - np.mean(last_polarity_score))
            last_p = 0
            cur_p = 0
            for p in last_self['polarity']: 
                if p['compound'] > 0.5: last_p = 1
            for p in action['polarity']: 
                if p['compound'] > 0.5: cur_p = 1
            if cur_p < last_p: ret['positive_decrease'] = 1
            if cur_p > last_p: ret['positive_increase'] = 1
    if total_gaps:
        ret['mean_toxicity_gap'] /= total_gaps
    return ret


