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

def attacker_profile(document, user_infos, ASPECTS):
    """
      Given the user information in conversations and a set of aspects to be inspected
      Returns the profile of the last participant in the conversation
      For a certain aspect(for example, age), 
      returns if the last participant's value is min, max or in the middle compared to other users.
      If all the users have the same value, return 'No Gap'.
      If the last participant only appeared at the end, return 'New Comer'.
      If the last participant doesn't have user name, return 'Anonymous'.
      If the last participant is a bot, return 'Bot'.
    """
    actions = document['action_feature']
    end_time = 0
    start_time = np.inf
    attacker = None
    for action in actions:
        if action['timestamp_in_sec'] > end_time:
            end_time = action['timestamp_in_sec'] 
            if 'user_text' in action:
                attacker = action['user_text']
            else:
                attacker = None
        start_time = min(start_time, action['timestamp_in_sec'])
    appeared = False
    for action in actions:
        if action['timestamp_in_sec'] < end_time:
            if 'user_text' in action and action['user_text'] == attacker:
                appeared = True
    blocked = False
    profile = {}
    for aspect in ASPECTS:
        profile[aspect] = 0

    if attacker and attacker in user_infos:
        profile = user_infos[attacker]
    cnts = {}
    for aspect in ASPECTS:
        mini = np.inf
        maxi = 0
        for u in user_infos.keys():
            if aspect in user_infos[u]:
                mini = min(user_infos[u][aspect], mini)
                maxi = max(user_infos[u][aspect], maxi)
        if attacker == None or 'anon' in profile:
            cnts[aspect] = 'Anonymous'
            continue
        if not(appeared):
            cnts[aspect] = 'New Comer'
            continue
        if 'bot' in profile:
            cnts[aspect] = 'Bot'
            continue
        if maxi > mini:
            if profile[aspect] == mini:
                cnts[aspect] = 'Min'
            else:
                if profile[aspect] == maxi:
                    cnts[aspect] = 'Max'
                else:
                    cnts[aspect] = 'In the Middle'
        else:
            cnts[aspect] = 'No Gap'
        cnts['experience'] = profile['comments_on_all_talk_pages']
    return cnts, blocked

def _user_features(actions, user_features, ASPECTS, STATUS):
    """
      Given user features collected for all users in the dataset, generates participant feature vectors and return the values of participant profiles for a particular conversation.
          - Parameters:
               - document: current conversation 
               - user_features: Wikipedia user features for all users in the dataset
               - ASPECTS: set of aspects(A subset of participant historical information)
               - STATUS: self defined grouping of user roles
          - Participant Feature:
               - For each aspect in ASPECTS, compute the max, min and entropy values of among pariticipants'.
               - has_anon: Conversation has anonymous participant
               - has_blocked: Conversation has participant with a block in history
               - has_bot: Converesation has a bot
          - Participant Behavior in the Conversation(to be passed on to compute attacker plot)
               - proportion_of_being_replied : # comments being replied / # comments posted by the participant
               - total_reply_time_gap : For all the comments that were replied, sum of the time between the reply and the comment.
               - proportion_of_utterance_over_all: # comments by the participant / # comments in the conversation
               - total_length_of_utterance: Total number of tokens in the participant's comments.
               - maximum_toxicity: Max of toxicity scores of comments of the participant.
               - pron_you_usage: Total number of usage of pronoun 'you' by the participant.
               - gratitude_usage: Total number of usage of words with gratitude by the participant.
               - max_negativity: Max of polarity score indicating negative polarity of comments by the participant.
               - reply_latency: Total number of the reply gap between replies by the participant and the post it replies to.
          - Participant History before the Conversation 
               - age: Number of the months since participant's registration 
               - status: Wikipedia user group of the participant 
               - comments_on_same_talk_page: Number of comments on the same talk page 
               - comments_on_all_talk_pages: Number of comments on all talk pages 
               - edits_on_subjectpage: Number of edits on the corresponding wikipedia article pages 
               - edits_on_wikipedia_articles: Number of edits on the all wikipedia article pages 
               - history_toxicity: Average toxicity score of the most recent 100 comments posted by the participant at least a week before the conversation. 
    """
    # Initialization 
    EPS = 0.001
    start_time = min([a['timestamp_in_sec'] for a in actions])

    users = []
    user_infos = {}

    total_utterances = 0
    ret = {'has_anon': 0, 'has_bot':0, 'has_blocked' : 0}
    action_dict = {}
    replied = {}
    # Collecting participant list
    for action in actions:
        total_utterances += 1
        action_dict[action['id']] = action
        if 'user_text' in action:
            users.append(action['user_text'])
        else:
            ret['has_anon'] = 1
    # Initialization 
    total = {}
    lst = {}
    for aspect in ASPECTS:
        ret['%s_gap'%aspect] = 0
        ret['min_%s'%aspect] = np.inf
        ret['max_%s'%aspect] = 0
        ret['%s_entropy'%aspect] = 1
        total[aspect] = 0
        lst[aspect] = []

    bot = ['bot']
      
    # Initialize participant behavior
    # Collect participant history 
    for u in users:
        user_info = {'proportion_of_being_replied' : 0, 'total_reply_time_gap' : 0, \
                'proportion_of_utterance_over_all': 0, 'total_length_of_utterance': 0, \
                 'maximum_toxicity' : 0, 'pron_you_usage': 0, \
                    'gratitude_usage' : 0, 'max_negativity': 0, 'reply_latency': 0}
        if u in user_features:
            user = user_features[u]
            if 'blocked' in user:
                ret['has_blocked'] = 1
                user_info['blocked'] = 1
            if 'registration' in user:
                user_info['age'] = max(0, (start_time - user['registration']) / 60 / 60 / 24 / 30)
            else:
                ret['has_anon'] = 1
                user_info['anon'] = 1
                user_info['age'] = 0
            level = 0
            if 'groups' in user:
                for g in user['groups']:
                    if g in bot:
                        ret['has_bot'] = 1
                        level = -1
                        break
                    for l in STATUS.keys():
                        if g in STATUS[l]:
                            level = max(level, l)
            if level >= 0:
                user_info['status'] = level
                user_info['comments_on_same_talk_page'] = user['edits_on_this_talk_page']
                user_info['comments_on_all_talk_pages'] = user['edits_on_wikipedia_talks']
                user_info['edits_on_subjectpage'] = user['edits_on_subjectpage']
                user_info['edits_on_wikipedia_articles'] = user['edits_on_wikipedia_articles']
            else:
                user_info['bot'] = 1
            user_info['history_toxicity'] = user['history_toxicity']
        else:
            ret['has_anon'] = 1
            user_info['anon'] = 1
            for aspect in ASPECTS:
                user_info[aspect] = 0
        if 'status' in user_info:
            for aspect in ASPECTS:
                ret['max_%s'%aspect] = max(ret['max_%s'%aspect], user_info[aspect])
                ret['min_%s'%aspect] = min(ret['min_%s'%aspect], user_info[aspect])
                total[aspect] += user_info[aspect]
                lst[aspect].append(user_info[aspect])
        user_infos[u] = user_info

    # Collect participant behavior
    for action in actions:
        if not(action['comment_type'] == 'SECTION_CREATION' or action['comment_type'] == 'COMMENT_ADDING'):
            continue
        if 'user_text' in action:
            user = action['user_text']
            user_infos[user]['total_length_of_utterance'] += len(action['unigrams'])
            user_infos[user]['maximum_toxicity'] = max(user_infos[user]['maximum_toxicity'], action['score'])
            user_infos[user]['pron_you_usage'] += action['pron_you']
            user_infos[user]['proportion_of_utterance_over_all'] += 1
            user_infos[user]['gratitude_usage'] += sum([not(str.find(u.lower(), 'thank')==-1)  for u in action['unigrams']])
            if not(action['polarity'] == []):
                cur_neg = max([p['neg'] for p in action['polarity']])
            else:
                cur_neg = 0
            user_infos[user]['max_negativity'] = max(user_infos[user]['max_negativity'], cur_neg)
            if not('replyTo_id' not in action or action['replyTo_id'] == None):
                replied[action['replyTo_id']] = action['timestamp_in_sec']
                user_infos[user]['reply_latency'] += action['timestamp_in_sec'] - action_dict[action['replyTo_id']]['timestamp_in_sec']
    for key in replied.keys():
        if 'user_text' in action_dict[key]:
            user = action_dict[key]['user_text']
            user_infos[user]['proportion_of_being_replied'] += 1
            user_infos[user]['total_reply_time_gap'] += replied[key] - action_dict[key]['timestamp_in_sec']
    for u in user_infos.keys():
        for key in ['proportion_of_being_replied']:
            if user_infos[u]['proportion_of_utterance_over_all']:
               user_infos[u][key] /= user_infos[u]['proportion_of_utterance_over_all']
        user_infos[u]['proportion_of_utterance_over_all'] /= total_utterances

    # Compute pariticipant features 
    for aspect in ASPECTS:
        if len(lst[aspect]):
            ret['%s_gap'%(aspect)] = ret['max_%s'%aspect] - ret['min_%s'%aspect]
            if len(lst[aspect]) > 1 and total[aspect]:
                l = len(lst[aspect])
                for x in lst[aspect]:
                    if x == 0:
                        a = EPS
                    else:
                        a = x
                ret['%s_entropy'%aspect] += a / total[aspect] * math.log(a / total[aspect]) / math.log(l)
        else:
            ret['%s_entropy'%aspect] = 0
        if np.isinf(ret['min_%s'%aspect]):
            ret['min_%s'%(aspect)] = 0
    return ret, user_infos

