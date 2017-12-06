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


def _get_balance_features(actions):
    """
       Two definitions of notions:
          - nouns over tokens: # of distinct nouns used / # of all nouns
          - entropy of set S:
               - if |S| <= 1, entropy = 0
               - for s in S, if s = 0, set s = EPS
               - normalize S
               - entropy = 1 + \Sigma(s * log(s)/log(|S|))
       1) Extracts features that reflects the interaction between an utterance U and the utterance replying to it R.
           - question_to_question: has a pair of U and R such that both U and R contain a question
           - question_to_non_question: has a pair of U and R such that U doesn't have a question, R contains a question
           - non_question_to_question: has a pair of U and R such that R doesn't have a question, U contains a question
           - has_content_words_adoption: has a pair of U and R such that R repeats a non stopwords in U
           - has_stopwords_adoption: has a pair of U and R such that R repeats a stopword in U
           - max_time_gap: maximum time gap between U and R
           - frac. negative_reply: # U and R pairs such that R contains negative polarity / # U and R pairs
           - positive reply to negative: has a pair of U and R such that U contains negative polarity and R contains positive polarity
           - negative reply to positive: has a pair of U and R such that U contains positive polarity and R contains negative polarity
       2) Extracts features of each participant's behavior in the conversation: 
           - max_nouns_over_tokens: maximum nouns over tokens ratio among participants 
           - min_nouns_over_tokens: minimum nouns over tokens ratio among participants 
           - nouns_over_tokens_entropy: entropy of nouns over tokens ratio among participants
       3) Extracts features of reply relations among participants:
           - interaction_density: # participant reply pairs / (# participants)^2
           - max_depth: maximum reply thread length
           - reciprocity: # particpants reply to each other / # participant reply pairs
           - reply_entropy: entropy of replies a participant received 
           - time_gap_entropy: entropy of (sum of the reply time gaps over all replies received by a participant) 
           - action_no_entropy: entropy of number of utterances from a participant
           - length_entropy: entropy of total length of utterances from a participant
       4) Extracts global nouns over tokens features:
           - nouns_over_tokens: global nouns over tokens ratio
    """ 
    # Initialize
    EPS = 0.001
    unigrams, bigrams = set([]), set([])
    no_users = 0
    user_set = {}
    reply_no = {}
    action_no = defaultdict(int)
    time_gap = {}
    action_dict = {}
    total_user = 0
    lengths = {}
    all_nouns = []
    user_nouns = defaultdict(list)
    
    for action in actions:
        action_dict[action['id']] = action

    for action in actions:
        if not('user_text' in action):
            continue
        user_set[action['user_text']] = 1
        if not('bot' in action['user_text'].lower()):
            total_user += 1
        reply_no[action['user_text']] = EPS
        time_gap[action['user_text']] = EPS
        lengths[action['user_text']] = EPS
        action_no[action['user_text']] = EPS
    total_replyTo = len(reply_no.keys()) * EPS
    total_time = len(reply_no.keys()) * EPS
    total_length = len(reply_no.keys()) * EPS
    total_actions = len(reply_no.keys()) * EPS


    no_users = len(user_set.keys())
    ret = {'question_to_question': 0, 'question_to_non_question': 0, 'non_question_to_question': 0} 
    for adoption in ['content_words', 'stopwords']:
        ret['has_%s_adoption'%(adoption)] = 0 
    
    max_depth = 1
    reply_pair = defaultdict(int)
    unique_reply_pairs = {}
    self_replies = {}
    ret['max_time_gap'] = 0
    ret['has_negative_reply'] = 0
    ret['frac. negative_reply'] = 0
    ret['positive reply to negative'] = 0
    ret['negative reply to positive'] = 0
    all_replys = 0
    for action in actions:
        # Only consider actions that add comment to the conversation
        if action['comment_type'] == 'COMMENT_REMOVAL' or action['comment_type'] == 'COMMENT_RESTORATION'\
           or action['comment_type'] == 'COMMENT_MODIFICATION':
           continue
        poses = action['pos_tags_with_words']
        # Collect Nouns
        nouns = []
        for ind, p in enumerate(poses):
            if p[1][:2] == 'NN':
               nouns.append(action['unigrams'][ind])
        all_nouns = all_nouns + nouns
        # Compute noun usage, utterance length and number of utterance by a participant
        if 'user_text' in action:
            user = action['user_text']
            action_no[action['user_text']] += 1
            total_actions += 1
            user_nouns[user] = user_nouns[user] + nouns
            total_length += action['length']
            lengths[action['user_text']] += action['length']
        # Get polarity label
        is_negative = 0
        is_positive = 0
        for p in action['polarity']:
            polarity = p['compound']#, polarity)
            is_negative = is_negative or (p['compound'] < -0.5)
            is_positive = is_positive or (p['compound'] > 0.5)
            if p['compound'] > 0.5: 
                polarity = 3
            elif polarity < - 0.5:
                polarity = 1
            else: polarity = 2
        if not('replyTo_id' not in action or action['replyTo_id'] == None):
            # Find the utterance that the current one is replying to
            parent = action_dict[action['replyTo_id']]
            # If the current utterance contains negative polarity
            ret['has_negative_reply'] = ret['has_negative_reply'] or is_negative
            ret['frac. negative_reply'] += is_negative
            # The polarities of the reply pair
            if is_negative:
               parent_polar = 0
               has_pos = 0
               has_neg = 0
               for p in parent['polarity']:
                   has_pos = has_pos or (p['compound'] > 0.5) 
                   has_neg = has_neg or (p['compound'] < -0.5) 
               if has_pos and is_negative:
                  ret['negative reply to positive'] = 1
               if has_neg and is_positive:
                  ret['positive reply to negative'] = 1
            all_replys += 1
            # Compute the longest reply thread
            d = 2
            cur = parent
            while not('replyTo_id' not in cur or cur['replyTo_id'] == None):
                cur = action_dict[cur['replyTo_id']]
                d += 1
            max_depth = max(max_depth, d)
            # Compute the reply pair
            if 'user_text' in parent and 'user_text' in action:
                reply_pair[(parent['user_text'], action['user_text'])] += 1
                unique_reply_pairs[(min(parent['user_text'], action['user_text']), \
                            max(parent['user_text'], action['user_text']))] = 1
                if parent['user_text'] == action['user_text']:
                    self_replies[action['user_text']] = 1
            
            # The question asking and answering pattern of the reply pair 
            if '?' in action['unigrams'] and  '?' in parent['unigrams']:
                ret['question_to_question'] = 1
            if '?' in action['unigrams'] and  not('?' in parent['unigrams']):
                ret['question_to_non_question'] = 1
            if not('?' in action['unigrams']) and  '?' in parent['unigrams']:
                ret['non_question_to_question'] = 1
            # Compute reply time gap
            if 'user_text' in parent:
                reply_no[parent['user_text']] += 1
                time_gap[parent['user_text']] += action['timestamp_in_sec'] - parent['timestamp_in_sec']
            total_time += action['timestamp_in_sec'] - parent['timestamp_in_sec']
            ret['max_time_gap'] = max(ret['max_time_gap'], action['timestamp_in_sec'] - parent['timestamp_in_sec'])
            total_replyTo += 1
            # Compute word adoption
            for adoption in ['content_words', 'stopwords']:
                cur_adoption = (len(set(action[adoption]) & set(parent[adoption])) > 0)
                if cur_adoption > 0:
                    ret['has_%s_adoption'%(adoption)] = 1 
    # Compute interaction density
    if no_users:
        ret['interaction_density'] = len(reply_pair.keys()) / (no_users * no_users)
    else:
        ret['interaction_density'] = 0
    # Compute negative reply fractoin
    if all_replys:
        ret['frac. negative_reply'] /= all_replys
        
    # Compute nouns to tokens ratio
    all_users = sorted(user_set.keys())
    if all_nouns:
       ret['nouns_over_tokens'] = len(set(all_nouns)) / float(len(all_nouns))
    else:
       ret['nouns_over_tokens'] = 0
    nounlst = []
    for user in user_nouns.values():
        if len(user):
           nounlst.append(len(set(user))/float(len(user)))
    if nounlst == []:
       ret['max_nouns_over_tokens'] = 0 
       ret['min_nouns_over_tokens'] = 0
    else:
       ret['max_nouns_over_tokens'] = max(nounlst)
       ret['min_nouns_over_tokens'] = min(nounlst)
    ret['nouns_over_tokens_entropy'] = 1
    if len(nounlst) > 1:
       l = len(nounlst)
       s = sum(nounlst)
       entropy = 1
       for n in nounlst:
           entropy += n / s * math.log(n / s) / math.log(l)
       ret['nouns_over_tokens_entropy'] = entropy
    else:
       ret['nouns_over_tokens_entropy'] = 0
    # Compute pariticipant reply relation features
    total_reply_pairs = 0
    double_replys = 0
    for ind1, user1 in enumerate(all_users):
        for ind2, user2 in enumerate(all_users[ind1+1:]):
            pair1 = max(reply_pair[(user1, user2)], reply_pair[(user2, user1)])
            pair2 = min(reply_pair[(user1, user2)], reply_pair[(user2, user1)])
            if pair1 > 0 and pair2 > 0:
               double_replys += 1
            if pair1 > 0:
               total_reply_pairs += 1
    if total_reply_pairs:
       ret['reciprocity'] = double_replys / total_reply_pairs
    else:
       ret['reciprocity'] = 0

    ret['max_depth'] = max_depth
      
    # Compute entropies 
    no_users = len(reply_no.keys()) 
    ret['action_no_entropy'] = not(no_users <= 1)
    ret['reply_entropy'] = not(no_users <= 1)
    ret['time_gap_entropy'] = not(no_users <= 1)
    ret['length_entropy'] = not(no_users <= 1)
    for user in reply_no.keys():
        if no_users > 1:
            ret['reply_entropy'] += reply_no[user] / total_replyTo \
                    * math.log(reply_no[user] / total_replyTo) / math.log(no_users)
            ret['time_gap_entropy'] += time_gap[user] / total_time \
                    * math.log(time_gap[user] / total_time) / math.log(no_users)
            ret['action_no_entropy'] += action_no[user] / total_actions \
                    * math.log(action_no[user] / total_actions) / math.log(no_users)
            ret['length_entropy'] += lengths[user] / total_length \
                    * math.log(lengths[user] / total_length) / math.log(no_users)
    return ret


