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


# Extracts comment level conversational features from the last N comments
# N determined by parameter cnt
def _get_last_n_action_features(actions, cnt, LEXICONS):
    """
      Extracts linguistic features at utterance level from last N utterances in a conversation.
          - Parameters: 
               - cnt: N
               - LEXICONS: dictionary of predefined lexicons
          - Features colloected:
              - Linguistic features at utterance level:
                    - has_positive: has utterance contain positive polarity
                    - has_negative: has utterance contain negative polarity
                    - has_polite: has utterance that's a request and being classified as polite
                    - has_agree: has utterance contain lexicon showing aggreement
                    - has_disagree: has utterance contain lexicon showing disagreement
                    - has_greetings: has utterance contain greetings
                    - has_all_cap: has utterance contain words that's capitalized 
                    - has_consecutive_?or!: has utterance contain consecutive ? and !
                    - verb start: has utterance contain sentence that starts with a verb
                    - do/don't start: has utterance contain sentence that starts with do or don't
                    - has_thank: has utterance constain words expressing gratitude
                    - you_start: has utterance that starts with a you 

    """
    # Initialization
    unigrams, bigrams = set([]), set([])
    ret = {'has_positive': 0, 'has_negative': 0, 'has_polite': 0,\
           'has_agree' : 0, 'has_disagree': 0, \
           'has_greetings': 0, 'has_all_cap': 0, 'has_consecutive_?or!': 0, 'verb start': 0, \
           'do/don\'t start': 0, 'has_thank': 0, 'you_start': 0}
    for key in LEXICONS.keys():
        ret['LEXICON_' + key] = 0
    the_action = {}
    for action in actions:
        the_action[action['id']] = action
   
    # Collect Feature Vector
    num = cnt
    for action in actions:
        cnt -= 1
        if cnt == 0:
            break
        # Lexicons with agreement or disagreement
        ret['has_agree'] = ret['has_agree'] or action['has_agree']
        ret['has_disagree'] = ret['has_disagree'] or action['has_disagree']

        # Lexicons expressing greetings or gratitude
        unigrams = [u.lower() for u in action['unigrams']]
        ret['has_thank'] = ret['has_thank'] or ('thank' in unigrams) or ('thanks' in unigrams) or \
                           ('appreciated' in unigrams)
        ret['has_greetings'] = ret['has_greetings'] or ('hi' in unigrams) or ('hello' in unigrams) or \
                               ('hey' in unigrams)
        # Utterance containing consecutive ? or !
        if not(unigrams == []):
            pre_u = unigrams[0]
            for u in unigrams[1:]:
                if u in ['!', '?'] and pre_u in ['!', '?']:
                    ret['has_consecutive_?or!'] = 1
                pre_u = u
        # Sentence starts with do, don't or you        
        for s in action['sentences']:
            if s.lower().startswith('do ') or s.lower().startswith('don\'t '):
                ret['do/don\'t start'] = 1
            if s.lower().startswith('you ') or s.lower().startswith('you\'re '):
                ret['you_start'] = 1
        # Sentence starts with a verb
        for p in action['pos_tags']:
            if p[0] == 'VB':
                ret['verb start'] = 1
        # All capitalized words 
        for u in action['unigrams']:
            if len(u) > 1 and u == u.upper():
                ret['has_all_cap'] = 1
        # Utterance contain negative/positive polarity 
        polarity = []
        for p in action['polarity']:
            if p['compound'] < -0.5:
                ret['has_negative'] = 1
            if p['compound'] > 0.5:
                ret['has_positive'] = 1
        # Sentence with polite request 
        if action['is_request']:
            if action['politeness_score']['polite'] >= 0.5:
                ret['has_polite'] = 1
        # Sentence with predefined lexicon 
        for key in LEXICONS.keys():
            if action[key]: ret['LEXICON_' + key] = 1
    new_ret = {}
    # Change feature names 
    for key in ret.keys():
        new_ret['last_%d_'%num + key] = ret[key]
    return new_ret

def _get_action_features(actions, LEXICONS):
    """
      Extracts linguistic features at utterance level for last utterances from each participant.
          - Parameters: 
               - LEXICONS: dictionary of predefined lexicons
          - Features colloected:
              - Linguistic features at utterance level:
                    - has_positive: has utterance contain positive polarity
                    - has_negative: has utterance contain negative polarity
                    - has_polite: has utterance that's a request and being classified as polite
                    - has_agree: has utterance contain lexicon showing aggreement
                    - has_disagree: has utterance contain lexicon showing disagreement
                    - has_greetings: has utterance contain greetings
                    - has_all_cap: has utterance contain words that's capitalized 
                    - has_consecutive_?or!: has utterance contain consecutive ? and !
                    - verb start: has utterance contain sentence that starts with a verb
                    - do/don't start: has utterance contain sentence that starts with do or don't
                    - has_thank: has utterance constain words expressing gratitude
                    - predefined lexicon features
    """
    # Initialization
    ret = {'has_positive': 0, 'has_negative': 0, 'has_polite': 0, \
           'has_agree' : 0, 'has_disagree': 0, \
           'has_greetings': 0, 'has_all_cap': 0, 'has_consecutive_?or!': 0, 'verb start': 0, \
           'do/don\'t start': 0, 'has_thank': 0}
    for key in LEXICONS.keys():
        ret['LEXICON_' + key] = 0
    appeared_users = {}
    # Generate feature vector
    for action in actions:
        # Only extracts features from the last utterance of each participant
        if 'user_text' in action:
            if action['user_text'] in appeared_users:
                continue
            appeared_users[action['user_text']] = 1
        # Lexicons expressing agreement or disagreement
        unigrams = [u.lower() for u in action['unigrams']]
        ret['has_agree'] = ret['has_agree'] or action['has_agree']
        ret['has_disagree'] = ret['has_disagree'] or action['has_disagree']
        # Lexicons expressing gratitude or greetings 
        ret['has_thank'] = ret['has_thank'] or ('thank' in unigrams) or ('thanks' in unigrams) or \
                           ('appreciated' in unigrams)
        ret['has_greetings'] = ret['has_greetings'] or ('hi' in unigrams) or ('hello' in unigrams) or \
                               ('hey' in unigrams)
        # Utterances contain consecutive ? and !
        if not(unigrams == []):
            pre_u = unigrams[0]
            for u in unigrams[1:]:
                if u in ['!', '?'] and pre_u in ['!', '?']:
                    ret['has_consecutive_?or!'] = 1
                pre_u = u
        # Sentences start with do or don't       
        for s in action['sentences']:
            if s.lower().startswith('do ') or s.lower().startswith('don\'t '):
                ret['do/don\'t start'] = 1
        # Sentences start with verb
        for p in action['pos_tags']:
            if p[0] == 'VB':
                ret['verb start'] = 1
        # All capitalized words 
        for u in action['unigrams']:
            if len(u) > 1 and u == u.upper():
                ret['has_all_cap'] = 1
        # Polarity
        polarity = []
        for p in action['polarity']:
            if p['compound'] < -0.5:
                ret['has_negative'] = 1
            if p['compound'] > 0.5:
                ret['has_positive'] = 1
        # Politeness
        if action['is_request']:
            if action['politeness_score']['polite'] >= 0.5:
                ret['has_polite'] = 1
        # Predefined lexicons 
        for key in LEXICONS.keys():
            if action[ key]: ret['LEXICON_' +key] = 1
    # Change name of the features
    new_ret = {}
    for key in ret.keys():
        new_ret['user_last_action_' + key] = ret[key]
    return new_ret

def _get_global_action_features(actions):
    """
      - Utterance length features in a conversation:
           - max_len, min_len, avg_len: maximum, minimum, average number of tokens in utterance
           - has_policy_intervention: has utterance contain wikipedia link refering to harassment/vandalism policy
           - max_toxicity: maximum toxicity score of utterances
           - toxicity_entropy: entropy of all toxicity score of all utterances
    """
    ret = {'max_len' : 0, 'min_len': np.inf, 'avg_len': [], 'max_toxicity': 0}
    ret['has_policy_intervention'] = 0
    toxicities = []
    total_toxicity = 0
    for action in actions:
        ret['max_len'] = max(ret['max_len'], len(action['unigrams'])) 
        ret['min_len'] = min(ret['max_len'], len(action['unigrams'])) 
        ret['max_toxicity'] = max(ret['max_toxicity'], action['score'])
        ret['avg_len'].append(len(action['unigrams']))
        for x in action['wiki_link']:
            cur_link = x.lower()
            if 'vandal' in cur_link.lower() or 'vandalism' in cur_link.lower() or\
                'harass' in cur_link.lower() or 'harassment' in cur_link.lower():
                ret['has_policy_intervention'] = 1
        toxicities.append(action['score'])
        total_toxicity += action['score']

    ret['avg_len'] = np.mean(ret['avg_len'])

    lt = len(toxicities)
    ret['toxicity_entropy'] = not(lt == 1)
    if lt > 1:
        for t in toxicities:
            ret['toxicity_entropy'] += t / total_toxicity * math.log(t / total_toxicity) / math.log(lt)
    if ret['toxicity_entropy'] > 1:
        ret['toxicity_entropy'] = 1

    return ret




