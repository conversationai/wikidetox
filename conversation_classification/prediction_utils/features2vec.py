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

def attacker_profile(document, user_infos, collected, ASPECTS):
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

def _get_question_features(conv_id, QUESTIONS):
    ret = {}
    for ind in range(8):
        ret['question_type%d'%(ind)] = 0
    if conv_id in QUESTIONS:
        for x in QUESTIONS[conv_id]:
            ret['question_type%d'%(x)] = 1
    return ret

def get_features(user_features, documents, ARGS, BOW = False, Conversational = False, User = False, ACTION_FEATURE = False, SNAPSHOT_LEN = False, Questions = False, COMMENT_LEN = True):
    STATUS, ASPECTS, attacker_profile_ASPECTS, LEXICONS, QUESTIONS, UNIGRAMS_LIST, BIGRAMS_LIST = ARGS 
    feature_sets = []
    bow_features = []
    colorcodes = {}
    color_cnt = 0
    for pair in documents:
        conversation, clss, conv_id = pair
        feature_set = {}
        actions = conversation['action_feature']
        end_time = max([a['timestamp_in_sec'] for a in actions])
        actions = [a for a in actions if a['timestamp_in_sec'] < end_time]
        actions = sorted(actions, \
                key=lambda k: (k['timestamp_in_sec'], k['id'].split('.')[1], k['id'].split('.')[2]))[::-1]
        feature_set.update(_get_term_features(actions, UNIGRAMS_LIST, BIGRAMS_LIST))
        for k in feature_set.keys():
            colorcodes[k] = color_cnt
        bow_features.append((copy.deepcopy(feature_set), clss))
    conv_features = []
    color_cnt += 1
    assigned = False
    for pair in documents:
        conversation, clss, conv_id = pair
        feature_set = {}
        actions = conversation['action_feature']
        end_time = max([a['timestamp_in_sec'] for a in actions])
        actions = [a for a in actions if a['timestamp_in_sec'] < end_time]
        actions = sorted(actions, \
                key=lambda k: (k['timestamp_in_sec'], k['id'].split('.')[1], k['id'].split('.')[2]))[::-1]
        feature_set.update(_get_last_n_action_features(actions, 1, LEXICONS, ACTION_FEATURE))
        if not(assigned):
            for k in feature_set.keys():
                if not(k in colorcodes):
                    colorcodes[k] = color_cnt
            color_cnt += 1
        feature_set.update(_get_action_features(actions, LEXICONS))
        if not(assigned):
            for k in feature_set.keys():
                if not(k in colorcodes):
                    colorcodes[k] = color_cnt
            color_cnt += 1          
        feature_set.update(_get_repeatition_features(actions))
        if not(assigned):
            for k in feature_set.keys():
                if not(k in colorcodes):
                    colorcodes[k] = color_cnt
            color_cnt += 1
        if Questions:
            feature_set.update(_get_question_features(conv_id, QUESTIONS))
            if not(assigned):
                for k in feature_set.keys():
                    if not(k in colorcodes): 
                        colorcodes[k] = color_cnt
                color_cnt += 1
        actions = actions[::-1]
        try:
            feature_set.update(_get_balance_features(actions))
        except:
            print([(a['id'], a['parent_id'], a['comment_type']) if 'parent_id' in a \
                   else (a['id'], a['comment_type'])for a in actions])
            break
        if not(assigned):
            for k in feature_set.keys():
                if not(k in colorcodes):
                    colorcodes[k] = color_cnt
            color_cnt += 1
            assigned = True
        if SNAPSHOT_LEN:
            feature_set['snapshot_len'] = conversation['snapshot_len']
        conv_features.append((copy.deepcopy(feature_set), clss))
    participant_features = []
    starter_attack_profiles = {0: [], 1:[]}
    non_starter_attack_profiles = {0: [], 1: []}
    all_profiles = {0: [], 1: []}
    blocks = []
    user_info = []
    assigned = False
    
    for ind, pair in enumerate(documents):
        conversation, clss, conv_id = pair
        actions = conversation['action_feature']
        start_time = min([a['timestamp_in_sec'] for a in actions])
        end_time = max([a['timestamp_in_sec'] for a in actions])
        for a in actions:
            if a['timestamp_in_sec'] == start_time:
                if 'user_text' in a:
                    starter = a['user_text']
                else:
                    starter = 'anon'
            if a['timestamp_in_sec'] == end_time:
                if 'user_text' in a:
                    ender = a['user_text']
                else:
                    ender = 'anon'
        feature_set, user_infos = _user_features(conversation, user_features[conv_id], ASPECTS, STATUS)
        if not(assigned):
            for k in feature_set.keys():
                if not(k in colorcodes):
                    colorcodes[k] = color_cnt
            color_cnt += 1
            assigned = True
        p, b = attacker_profile(conversation,  user_infos, feature_set, attacker_profile_ASPECTS)
        user_info.append(user_infos)
        if starter == ender:
            starter_attack_profiles[clss].append(p)
        else:
            non_starter_attack_profiles[clss].append(p)
        all_profiles[clss].append(p)
        blocks.append(int(b))
        participant_features.append((copy.deepcopy(feature_set), clss))
    feature_sets = []

    for ind, pair in enumerate(documents):
        conversation, clss, conv_id = pair
        actions = conversation['action_feature']
        end_time = max([a['timestamp_in_sec'] for a in actions])
        actions = [a for a in actions if a['timestamp_in_sec'] < end_time]
        comments_actions = [a for a in actions if a['comment_type'] == 'SECTION_CREATION' or a['comment_type'] == 'COMMENT_ADDING']

        feature_set = {}
        if COMMENT_LEN: 
           feature_set = {'no_comments': len(comments_actions)} 
        if BOW:
            feature_set.update(bow_features[ind][0])
        if Conversational:
            feature_set.update(conv_features[ind][0])
        if User:
            feature_set.update(participant_features[ind][0])
        feature_sets.append((feature_set, clss))
    return user_info, starter_attack_profiles, non_starter_attack_profiles, all_profiles, feature_sets, colorcodes

def _user_features(document, user_features, ASPECTS, STATUS):
    EPS = 0.001

    actions = document['action_feature']
    end_time = 0
    start_time = np.inf
    for action in actions:
        if action['timestamp_in_sec'] > end_time:
            end_time = action['timestamp_in_sec'] 
        start_time = min(start_time, action['timestamp_in_sec'])

    users = []
    user_infos = {}

    total_utterances = 0
    ret = {'has_anon': 0, 'has_bot':0}
    action_dict = {}
    replied = {}
    for action in actions:
        if action['timestamp_in_sec'] == end_time:
            continue
        total_utterances += 1
        action_dict[action['id']] = action
        if 'user_text' in action:
            users.append(action['user_text'])
        else:
            ret['has_anon'] = 1
            
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

    for u in users:
        user_info = {'proportion_of_being_replied' : 0,\
                     'total_reply_time_gap' : 0, \
                'proportion_of_utterance_over_all': 0, 'total_length_of_utterance': 0, \
                 'maximum_toxicity' : 0, \
                    'pron_you_usage': 0, \
                    'gratitude_usage' : 0, 'max_negativity': 0, \
                    'reply_latency': 0}
        if u in user_features:
            user = user_features[u]
            if 'blocked' in user:
                ret['has_blocked'] = 1
                user_info['blocked'] = 1
            if 'registration' in user:
                user_info['age'] = max(0, (start_time - user['registration']) / 60 / 60 / 24 / 30)
                
                if user_info['age']:
                    if user_info['age'] < 1:
                        user_info['age'] = 1
                    elif user_info['age'] <= 6:
                        user_info['age'] = 6
                    elif user_info['age'] <= 12:
                        user_info['age'] = 12
                    elif user_info['age'] <= 18:
                        user_info['age'] = 18
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
        if 'status' in user_info:# and not('anon' in user_info): # is bot
            for aspect in ASPECTS:
                ret['max_%s'%aspect] = max(ret['max_%s'%aspect], user_info[aspect])
                ret['min_%s'%aspect] = min(ret['min_%s'%aspect], user_info[aspect])
                total[aspect] += user_info[aspect]
                lst[aspect].append(user_info[aspect])
        user_infos[u] = user_info
    for action in actions:
        if action['timestamp_in_sec'] == end_time:
            continue
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
               # user_infos[user]['proportion_of_replies_to_others'] += 1
            #if action['comment_type'] == 'COMMENT_MODIFICATION':
            #    if 'parent_id' in action and action['parent_id'] in action_dict:
            #        if not('bot' in user):
                     #   user_infos[user]['bot_modification'] += 1
            #        else:
            #            parent = action_dict[action['parent_id']]
            #            if 'user_text' in parent:
            #                if parent['user_text'] == user:
            #                    user_infos[user]['self_modification'] += 1 
            #                else:
            #                    user_infos[user]['other_modification'] += 1
            #            else:
            #                user_infos[user]['other_modification'] += 1

            #    else:
            #         user_infos[user]['other_modification'] += 1
    for key in replied.keys():
        if 'user_text' in action_dict[key]:
            user = action_dict[key]['user_text']
            user_infos[user]['proportion_of_being_replied'] += 1
            user_infos[user]['total_reply_time_gap'] += replied[key] - action_dict[key]['timestamp_in_sec']
    for u in user_infos.keys():
        for key in ['proportion_of_being_replied']:
                   #'self_modification', 'other_modification']:
            if user_infos[u]['proportion_of_utterance_over_all']:
               user_infos[u][key] /= user_infos[u]['proportion_of_utterance_over_all']
        user_infos[u]['proportion_of_utterance_over_all'] /= total_utterances
    entropies = {}
    for aspect in ASPECTS:
        if len(lst[aspect]):
            ret['%s_gap'%(aspect)] = ret['max_%s'%aspect] - ret['min_%s'%aspect]
#            ret['%s_variance'%(aspect)] = np.var(lst[aspect])
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
        entropies['%s_entropy'%aspect] = ret['%s_entropy'%aspect]
 #   print(ret['max_age'])
  #  return entropies, user_infos
    return ret, user_infos#ret, user_infos # non_starter_attacker_profiles

def _get_term_features(actions, UNIGRAMS_LIST, BIGRAMS_LIST):
    unigrams, bigrams = set([]), set([])
    f = {}
    for action in actions:
        if not(action['comment_type'] == 'COMMENT_ADDING' or\
                action['comment_type'] == 'SECTION_CREATION'):
            continue
        unigrams = unigrams | set(action['unigrams'])
        bigrams = bigrams | set([tuple(x) for x in action['bigrams']]) 
    f.update(dict(map(lambda x: ("UNIGRAM_" + str(x), 1 if x in unigrams else 0), UNIGRAMS_LIST)))
    f.update(dict(map(lambda x: ("BIGRAM_" + str(x), 1 if tuple(x) in bigrams else 0), BIGRAMS_LIST)))
    return f 

def _get_last_n_action_features(actions, cnt, LEXICONS, ACTION_FEATURE=False):
    unigrams, bigrams = set([]), set([])
    ret = {'has_positive': 0, 'has_negative': 0, 'has_polite': 0,'has_deletion' : 0, \
        'has_modification': 0, 'has_restoration': 0, 'has_agree' : 0, 'has_disagree': 0, \
           'has_greetings': 0, 'has_all_cap': 0, 'has_consecutive_?or!': 0, 'verb start': 0, \
           'do/don\'t start': 0, 'has_thank': 0, 'you_start': 0, \
	   'self_modification': 0, 'bot_modification': 0, 'other_modification': 0, \
	'max_len' : 0, 'min_len': np.inf, 'avg_len': []}
    for key in LEXICONS.keys():
        ret['LEXICON_' + key] = 0
    the_action = {}
    for action in actions:
        the_action[action['id']] = action
    appeared_users = {}
    negative = 0
    positive = 0
    num = cnt
    for action in actions:
        if action['comment_type'] == 'COMMENT_REMOVAL':
            if (ACTION_FEATURE): ret['has_deletion'] = 1
            continue
        elif action['comment_type'] == 'COMMENT_RESTORATION':
            if (ACTION_FEATURE): ret['has_restoration'] = 1
            continue
        elif action['comment_type'] == 'COMMENT_MODIFICATION':
            if (ACTION_FEATURE):  
              ret['has_modification'] = 1
              if 'user_text' in action and action['parent_id'] in the_action:
                 if 'bot' in action['user_text'].lower():
                     ret['bot_modification'] = 1
                 else:
                     parent = the_action[action['parent_id']]
                     if 'user_text' in parent:
                        if parent['user_text'] == action['user_text']:
                           ret['self_modification'] = 1 
                        else:
                           ret['other_modification'] = 1
                     else:
                        ret['other_modification'] = 1
              else:
                 ret['other_modification'] = 1
            continue
        ret['max_len'] = max(ret['max_len'], len(action['unigrams'])) 
        ret['min_len'] = min(ret['max_len'], len(action['unigrams'])) 
        ret['avg_len'].append(len(action['unigrams']))
        cnt -= 1
        if cnt == 0:
            break

        ret['has_agree'] = ret['has_agree'] or action['has_agree']
        ret['has_disagree'] = ret['has_disagree'] or action['has_disagree']
        
        unigrams = [u.lower() for u in action['unigrams']]
        ret['has_thank'] = ret['has_thank'] or ('thank' in unigrams) or ('thanks' in unigrams) or \
                           ('appreciated' in unigrams)
        ret['has_greetings'] = ret['has_greetings'] or ('hi' in unigrams) or ('hello' in unigrams) or \
                               ('hey' in unigrams)
        
            
        if not(unigrams == []):
            pre_u = unigrams[0]
            for u in unigrams[1:]:
                if u in ['!', '?'] and pre_u in ['!', '?']:
                    ret['has_consecutive_?or!'] = 1
                pre_u = u
                
                
        for s in action['sentences']:
            if s.lower().startswith('do ') or s.lower().startswith('don\'t '):
                ret['do/don\'t start'] = 1
            if s.lower().startswith('you ') or s.lower().startswith('you\'re '):
                ret['you_start'] = 1
        for p in action['pos_tags']:
            if p[0] == 'VB':
                ret['verb start'] = 1

        
        
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
        
        for key in LEXICONS.keys():
            if action[key]: ret['LEXICON_' + key] = 1
    
    new_ret = {}
    ret['avg_len'] = np.mean(ret['avg_len'])
    for key in ret.keys():
        if not('_len' in key or 'modification' in key or 'deletion' in key or 'restoration' in key):
           new_ret['last_%d_'%num + key] = ret[key]
        else:
           new_ret[key] = ret[key]
    return new_ret

def _get_action_features(actions, LEXICONS):
    unigrams, bigrams = set([]), set([])
    ret = {'has_positive': 0, 'has_negative': 0, 'has_polite': 0, 'max_length': 0, 'has_deletion' : 0, \
        'has_modification': 0, 'has_restoration': 0, 'has_agree' : 0, 'has_disagree': 0, \
           'has_greetings': 0, 'has_all_cap': 0, 'has_consecutive_?or!': 0, 'verb start': 0, \
           'do/don\'t start': 0, 'has_thank': 0}
    for key in LEXICONS.keys():
        ret['LEXICON_' + key] = 0
    appeared_users = {}
    negative = 0
    positive = 0
    for action in actions:
        if action['comment_type'] == 'COMMENT_REMOVAL' \
           or action['comment_type'] == 'COMMENT_RESTORATION' \
           or action['comment_type'] == 'COMMENT_MODIFICATION':
             continue

        if 'user_text' in action:
            if action['user_text'] in appeared_users:
                continue
            appeared_users[action['user_text']] = 1

        unigrams = [u.lower() for u in action['unigrams']]
        ret['has_agree'] = ret['has_agree'] or action['has_agree']
        ret['has_disagree'] = ret['has_disagree'] or action['has_disagree']
        
        ret['has_thank'] = ret['has_thank'] or ('thank' in unigrams) or ('thanks' in unigrams) or \
                           ('appreciated' in unigrams)
        ret['has_greetings'] = ret['has_greetings'] or ('hi' in unigrams) or ('hello' in unigrams) or \
                               ('hey' in unigrams)
        
            
        if not(unigrams == []):
            pre_u = unigrams[0]
            for u in unigrams[1:]:
                if u in ['!', '?'] and pre_u in ['!', '?']:
                    ret['has_consecutive_?or!'] = 1
                pre_u = u
                
               
        for s in action['sentences']:
            if s.lower().startswith('do ') or s.lower().startswith('don\'t '):
                ret['do/don\'t start'] = 1

        for p in action['pos_tags']:
            if p[0] == 'VB':
                ret['verb start'] = 1
       
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
        
        for key in LEXICONS.keys():
            if action[ key]: ret['LEXICON_' +key] = 1

    new_ret = {}
    for key in ret.keys():
        new_ret['user_last_action_' + key] = ret[key]
    return new_ret

def _get_repeatition_features(actions):
    unigrams, bigrams = set([]), set([])
    ret = {'negative_increase': 0, 'positive_decrease': 0, 'toxicity_raise': 0, 'consecutive_negative': 0,
          'negative_decrease': 0, 'positive_increase': 0, 'max_toxicity': 0, 'max_toxicity_gap': 0, \
           'mean_toxicity_gap': 0, 'last_toxicity_gap': 0, 'max_polarity_gap': 0, 'has_policy_intervention': 0}
    self_feat = 0
    for repeat in ['content_words', 'stopwords']:
        ret['has_%s_repeat'%(repeat)] = 0
        ret['%s_repeat'%(repeat)] = 0
    appeared_users = {}
    repeat_users = {}
    total_gaps = 0
    for action in actions:  
        last_self = None
        if not('user_text' not in action or action['user_text'] == None):
            for act in actions:
                if not('user_text' not in act or act['user_text'] == None) and \
                   action['user_text'] == act['user_text'] and \
                   act['timestamp_in_sec'] < action['timestamp_in_sec'] and \
                   (action['comment_type'] == 'SECTION_CREATION' or \
		   action['comment_type'] == 'COMMENT_ADDING'):
                    if last_self == None or last_self['timestamp_in_sec'] < act['timestamp_in_sec']:                               
                        last_self = act
        if action['comment_type'] == 'COMMENT_REMOVAL' or action['comment_type'] == 'COMMENT_RESTORATION' \
            or action['comment_type'] == 'COMMENT_MODIFICATION':
                continue
        for x in action['wiki_link']:
            cur_link = x.lower()
            if 'vandal' in cur_link.lower() or 'vandalism' in cur_link.lower() or\
                'harass' in cur_link.lower() or 'harassment' in cur_link.lower():
                ret['has_policy_intervention'] = 1
        ret['max_toxicity'] = max(ret['max_toxicity'], action['score'])
        if 'user_text' in action:
            appeared_users[action['user_text']] = 1
        if not(last_self == None):
            if 'user_text' in action:
                repeat_users[action['user_text']] = 1
            for repeat in ['content_words', 'stopwords']:
                cur_repeat = (len(set(action[repeat]) & set(last_self[repeat])) > 0)
                if cur_repeat > 0:
                    ret['has_%s_repeat'%(repeat)] = 1 
                    if not(repeat == 'pos'):
                        ret['%s_repeat'%(repeat)] = max(ret['%s_repeat'%(repeat)], \
                                            cur_repeat / float(action['length']))
            if last_self['score'] < action['score'] - 0.05:
                ret['toxicity_raise'] = 1
            ret['max_toxicity_gap'] = max(ret['max_toxicity_gap'], action['score'] - last_self['score'])
            ret['last_toxicity_gap'] = action['score'] - last_self['score']
            ret['mean_toxicity_gap'] += action['score'] - last_self['score']
            total_gaps += 1
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
          #  self_feat += 1
    if total_gaps:
        ret['mean_toxicity_gap'] /= total_gaps
    if len(appeared_users.keys()):
        ret['repeat_percentage'] = len(repeat_users.keys()) / float(len(appeared_users.keys()))
    else:
        ret['repeat_percentage'] = 0
    return ret

def _get_balance_features(actions):
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
    ret = {'question_to_question': 0, 'question_to_non_question': 0, 'non_question_to_question': 0, \
            'has_question' : 0}
    for adoption in ['content_words', 'stopwords']:
        ret['has_%s_adoption'%(adoption)] = 0
        ret['%s_adoption'%(adoption)] = 0
    
    polarities = []
    toxicities = []
    total_polarity = 0
    total_toxicity = 0
    max_depth = 1
    reply_pair = defaultdict(int)
    unique_reply_pairs = {}
    self_replies = {}
    ret['max_time_gap'] = 0
    min_polar = -1
    max_polar = 1
    ret['has_negative_reply'] = 0
    ret['frac. negative_reply'] = 0
    ret['positive reply to negative'] = 0
    ret['negative reply to positive'] = 0
    all_replys = 0
    for action in actions:
        if action['comment_type'] == 'COMMENT_REMOVAL' or action['comment_type'] == 'COMMENT_RESTORATION'\
           or action['comment_type'] == 'COMMENT_MODIFICATION':
           continue
        poses = action['pos_tags_with_words']
        nouns = []
        for ind, p in enumerate(poses):
            if p[1][:2] == 'NN':
               nouns.append(action['unigrams'][ind])
        all_nouns = all_nouns + nouns
        if 'user_text' in action:
            user = action['user_text']
            action_no[action['user_text']] += 1
            total_actions += 1
            user_nouns[user] = user_nouns[user] + nouns
        if 'user_text' in action:
            user = action['user_text']
            total_length += action['length']
            lengths[action['user_text']] += action['length']
       # if not(action['polarity'] == []):
       #     polarity = action['polarity'][0]['compound']
       # else:
       #     polarity = 1
        is_negative = 0
        is_positive = 0
        for p in action['polarity']:
            min_polar = min(min_polar, p['compound'])
            max_polar = max(max_polar, p['compound'])
            polarity = p['compound']#, polarity)
            is_negative = is_negative or (p['compound'] < -0.5)
            is_positive = is_positive or (p['compound'] > 0.5)
            if p['compound'] > 0.5: 
                polarity = 3
            elif polarity < - 0.5:
                polarity = 1
            else: polarity = 2
            total_polarity += polarity
        toxicities.append(action['score'])
        total_toxicity += action['score']
        if not('replyTo_id' not in action or action['replyTo_id'] == None):
            parent = action_dict[action['replyTo_id']]
            ret['has_negative_reply'] = ret['has_negative_reply'] or is_negative
            ret['frac. negative_reply'] += is_negative
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
            d = 2
            cur = parent
            while not('replyTo_id' not in cur or cur['replyTo_id'] == None):
                cur = action_dict[cur['replyTo_id']]
                d += 1
            if 'user_text' in parent and 'user_text' in action:
                reply_pair[(parent['user_text'], action['user_text'])] += 1
                unique_reply_pairs[(min(parent['user_text'], action['user_text']), \
                            max(parent['user_text'], action['user_text']))] = 1
                if parent['user_text'] == action['user_text']:
                    self_replies[action['user_text']] = 1
            max_depth = max(max_depth, d)
            
            # question or not
            if '?' in action['unigrams'] and  '?' in parent['unigrams']:
                ret['question_to_question'] = 1
            if '?' in action['unigrams'] and  not('?' in parent['unigrams']):
                ret['question_to_non_question'] = 1
            if not('?' in action['unigrams']) and  '?' in parent['unigrams']:
                ret['non_question_to_question'] = 1
            if '?' in action['unigrams']:
                ret['has_question'] = 1
            if 'user_text' in parent:
                reply_no[parent['user_text']] += 1
                time_gap[parent['user_text']] += action['timestamp_in_sec'] - parent['timestamp_in_sec']
            total_time += action['timestamp_in_sec'] - parent['timestamp_in_sec']
            ret['max_time_gap'] = max(ret['max_time_gap'], action['timestamp_in_sec'] - parent['timestamp_in_sec'])
            total_replyTo += 1
            for adoption in ['content_words', 'stopwords']:
                cur_adoption = (len(set(action[adoption]) & set(parent[adoption])) > 0)
                if cur_adoption > 0:
                    ret['has_%s_adoption'%(adoption)] = 1 
                    if not(adoption == 'pos'):
                        ret['%s_adoption'%(adoption)] = max(ret['%s_adoption'%(adoption)], \
                                            cur_adoption / float(action['length']))
    if no_users:
#        ret['undirected_graph_density'] = len(unique_reply_pairs.keys()) / (no_users * no_users)
        ret['interaction_density'] = len(reply_pair.keys()) / (no_users * no_users)
#        ret['self_replies'] = len(self_replies.keys()) / no_users
    else:
#        ret['undirected_graph_density'] = 0
        ret['interaction_density'] = 0
#        ret[''] = 0
    if all_replys:
        ret['frac. negative_reply'] /= all_replys
        
    all_users = sorted(user_set.keys())
#    ret['imbalance_in_pairs'] = 0
#    for x in range(4):
#        ret['graph_feature_triad' + str(x)] = 0
#    ret['triad_imbalance'] = 0
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
         #   if pair1 and pair2:
         #       entropy =  pair2 / (pair1 + pair2) * math.log(pair2 / (pair1 + pair2))/ math.log(2) \
         #               + pair1 / (pair1 + pair2) * math.log(pair1 / (pair1 + pair2))/ math.log(2)
         #       ret['imbalance_in_pairs'] = max(ret['imbalance_in_pairs'], entropy)
         #   for ind3, user3 in enumerate(all_users[ind2+1:]):
         #       no_replied = ((user1, user2) in unique_reply_pairs) + \
         #                    ((user1, user3) in unique_reply_pairs) + \
         #                    ((user2, user3) in unique_reply_pairs)
         #       ret['graph_feature_triad' + str(no_replied)] += 1
         #       pairs = [reply_pair[(user1, user2)] + reply_pair[(user2, user1)], \
         #                reply_pair[(user1, user3)] + reply_pair[(user3, user1)], \
         #                reply_pair[(user3, user2)] + reply_pair[(user2, user3)]]
#                ret['triad_imbalance'] = max(pairs) - min(pairs)
    if total_reply_pairs:
       ret['reciprocity'] = double_replys / total_reply_pairs
    else:
       ret['reciprocity'] = 0
#    if no_users >= 3:
#        for x in range(4):
#            ret['graph_feature_triad' + str(x)] /= (no_users * (no_users - 1) * (no_users - 2) / 6)
    ret['no_users'] = no_users
#    ret['has_reply'] = 0
    ret['conversation_polarity_gap'] = max_polar - min_polar

    if total_replyTo > 0:
#        ret['has_reply'] = 1
        ret['reply_entropy'] = 0
        ret['time_gap_entropy'] = 0

    ret['max_depth'] = max_depth
    lp = len(polarities)
    ret['polarity_entropy'] = not(lp == 1)
    if lp > 1:
        for p in polarities:
            ret['polarity_entropy'] += p / total_polarity * math.log(p / total_polarity) / math.log(lp)
    if ret['polarity_entropy'] > 1:
        ret['polarity_entropy'] = 1
        
    lt = len(toxicities)
    ret['toxicity_entropy'] = not(lt == 1)
    if lt > 1:
        for t in toxicities:
            ret['toxicity_entropy'] += t / total_toxicity * math.log(t / total_toxicity) / math.log(lt)
    if ret['toxicity_entropy'] > 1:
        ret['toxicity_entropy'] = 1
        
    no_replies = len(reply_no.keys())
    no_time_gaps = len(time_gap.keys())
    no_actions = len(action_no.keys())
    no_lengths = len(lengths.keys())
    ret['action_no_entropy'] = not(no_actions == 1)
    ret['reply_entropy'] = not(no_replies == 1)
    ret['time_gap_entropy'] = not(no_time_gaps == 1)
    ret['length_entropy'] = not(no_lengths == 1)
#    ret['directed_graph_nodes_with_incoming_edge'] = 0
    for user in reply_no.keys():
#        if reply_no[user]:
#            ret['directed_graph_nodes_with_incoming_edge'] += 1
        if no_replies > 1:
            ret['reply_entropy'] += reply_no[user] / total_replyTo \
                    * math.log(reply_no[user] / total_replyTo) / math.log(no_replies)
        if no_time_gaps > 1:
            ret['time_gap_entropy'] += time_gap[user] / total_time \
                    * math.log(time_gap[user] / total_time) / math.log(no_time_gaps)
        if no_actions > 1:
            ret['action_no_entropy'] += action_no[user] / total_actions \
                    * math.log(action_no[user] / total_actions) / math.log(no_actions)
        if no_lengths > 1:
            ret['length_entropy'] += lengths[user] / total_length \
                    * math.log(lengths[user] / total_length) / math.log(no_lengths)
#    ret['directed_graph_nodes_with_incoming_edge'] /= no_users#len(reply_no.keys())
    return ret

def documents2feature_vectors(document_features):
    fks = False
    X, y = [], []
    cnt = 0
    max_X = {}
    for pair in document_features:
        conversation, clss = pair
        fs = conversation
        if not fks:
            fks = sorted(fs.keys())
            for f in fks:
                max_X[f] = fs[f]
        fv = [fs[f] for f in fks]
        for f in fks:
            max_X[f] = max(max_X[f], fs[f])
        cnt += 1
        X.append(fv)
        y.append(clss)
    for fv in X:
        for ind, f in enumerate(fks):
            if max_X[f] == 0: 
                continue
            fv[ind] /= max_X[f]
    X = csr_matrix(np.asarray(X))
    y = np.asarray(y)
    return X, y, fks
