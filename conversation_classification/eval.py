import json
import pickle as cPickle
import numpy as np

from sklearn import svm
import sklearn.utils
from scipy.sparse import csr_matrix
from sklearn.model_selection import GridSearchCV, cross_val_score
from sklearn.metrics import classification_report
import random
import matplotlib.pyplot as plt
from scipy.stats.stats import pearsonr


from collections import defaultdict
import math
from sklearn import preprocessing

from scipy.stats import spearmanr
from sklearn import linear_model
import re
import copy

import seaborn as sns
import pandas as pd
import scipy.stats
import statsmodels.stats.proportion
from sklearn.cross_validation import LeaveOneOut
from prediction_utils.show_examples import update, generate_snapshots, clean
from prediction_utils.features2vec import _get_term_features, _get_last_n_action_features,             _get_action_features, _get_repeatition_features, _get_balance_features, documents2feature_vectors
constraints = ['delta2_no_users_attacker_in_conv', 'delta2_no_users']
constraint = constraints[1]
suffix = ''
UNIGRAMS_FILENAME = "/scratch/wiki_dumps/expr_with_matching/%s/bow_features/unigram100%s.pkl"%(constraint, suffix)
BIGRAMS_FILENAME = "/scratch/wiki_dumps/expr_with_matching/%s/bow_features/bigram200%s.pkl"%(constraint, suffix)
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
ASPECTS = ['age', 'status', 'comments_on_same_talk_page', 'comments_on_all_talk_pages',        'edits_on_subjectpage', 'edits_on_wikipedia_articles', 'history_toxicity']
attacker_profile_ASPECTS = ['proportion_of_being_replied', 'proportion_of_utterance_over_all', 'total_length_of_utterance','maximum_toxicity', 'age', 'status', 'comments_on_all_talk_pages','edits_on_wikipedia_articles', 'history_toxicity','self_modification', 'other_modification', 'pron_you_usage','gratitude_usage', 'max_negativity']
with open("/scratch/wiki_dumps/expr_with_matching/user_features/all.json") as f:
    inp = json.load(f)
user_features = {}
for conv, users in inp:
    user_features[conv] = users
with open('feature_extraction/utils/lexicons') as f:
    LEXICONS = json.load(f)
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
        ret['%s_variance'%aspect] = 1
        lst[aspect] = []

    bot = ['bot']

    for u in users:
        user_info = {'proportion_of_being_replied' : 0,'proportion_of_utterance_over_all': 0, \
                 'total_length_of_utterance': 0, \
                 'maximum_toxicity' : 0, \
                   'self_modification': 0, 'other_modification': 0, 'pron_you_usage': 0, \
                    'gratitude_usage' : 0, 'max_negativity': 0}
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
                replied[action['replyTo_id']] = 1
               # user_infos[user]['proportion_of_replies_to_others'] += 1
            
            if action['comment_type'] == 'COMMENT_MODIFICATION':
                if 'parent_id' in action and action['parent_id'] in action_dict:
                    if not('bot' in user):
                     #   user_infos[user]['bot_modification'] += 1
            #        else:
                        parent = action_dict[action['parent_id']]
                        if 'user_text' in parent:
                            if parent['user_text'] == user:
                                user_infos[user]['self_modification'] += 1 
                            else:
                                user_infos[user]['other_modification'] += 1
                        else:
                            user_infos[user]['other_modification'] += 1

                else:
                     user_infos[user]['other_modification'] += 1
    for key in replied.keys():
        if 'user_text' in action_dict[key]:
            user = action_dict[key]['user_text']
            user_infos[user]['proportion_of_being_replied'] += 1
    for u in user_infos.keys():
        for key in ['proportion_of_being_replied',                    'self_modification', 'other_modification']:
            user_infos[u][key] /= user_infos[u]['proportion_of_utterance_over_all']
        user_infos[u]['proportion_of_utterance_over_all'] /= total_utterances
    entropies = {}
    for aspect in ASPECTS:
        if len(lst[aspect]):
            ret['%s_gap'%(aspect)] = ret['max_%s'%aspect] - ret['min_%s'%aspect]
            ret['%s_variance'%(aspect)] = np.var(lst[aspect])
            if len(lst[aspect]) > 1 and total[aspect]:
                l = len(lst[aspect])
                for x in lst[aspect]:
                    if x == 0:
                        a = EPS
                    else:
                        a = x
                ret['%s_entropy'%aspect] += a / total[aspect] * math.log(a / total[aspect]) / math.log(l)
        if np.isinf(ret['min_%s'%aspect]):
            ret['min_%s'%(aspect)] = 0
        entropies['%s_entropy'%aspect] = ret['%s_entropy'%aspect]
    return ret, user_infos
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
def train_svm(X, y, C, matched_pairs):
    print("Fitting")
    train_indices = []
    test_indices = []
    y_l = len(y)
    for pair in matched_pairs:
        train = []
        test = []
        for ind in range(y_l):
            if ind in pair:
                test.append(ind)
            else:
                train.append(ind)
        train_indices.append(train)
        test_indices.append(test)
   # print([len(t) for t in test_indices])
    lpo = zip(train_indices, test_indices)
    scores = cross_val_score(svm.LinearSVC(C=C), X, y, cv=lpo, scoring = 'accuracy')
    print("%0.3f (+/-%0.03f)"
           % (np.mean(scores), scipy.stats.sem(scores) * 1.96))
def preprocess(actions):
    action_dict = {}
    for action in actions:
        action_dict[action['id']] = action
    ret = []
    for action in actions:
        if action['comment_type'] == 'COMMENT_MODIFICATION':
            if not('parent_id' in action) or not(action['parent_id'] in action_dict):
                action['comment_type'] = 'COMMENT_ADDING'
                action['parent_id'] = None 
        ret.append(action)
    return ret

documents = []
with open('/scratch/wiki_dumps/expr_with_matching/%s/data/all%s.json'%(constraint, suffix)) as f:
    for line in f:
        conv_id, clss, conversation = json.loads(line)
        conversation['action_feature'] = preprocess(conversation['action_feature'])
        actions = sorted(conversation['action_feature'],                 key=lambda k: (k['timestamp_in_sec'], k['id'].split('.')[1], k['id'].split('.')[2]))
        end_time = max([a['timestamp_in_sec'] for a in actions])
        actions = [a for a in actions if a['timestamp_in_sec'] < end_time]
        snapshot = generate_snapshots(actions)
        conversation['snapshot_len'] = len(snapshot)
        documents.append((conversation, clss, conv_id)) 
random.shuffle(documents)
matched_pairs = []
doc_dic = {}
title_dic = defaultdict(list)
for ind, doc in enumerate(documents):
    conversation, clss, conv_id = doc
    doc_dic[conv_id] = ind
    title_dic[conversation['action_feature'][0]['page_title']].append(ind)
matched_pairs = list(title_dic.values())
print(len(matched_pairs))

def get_features(BOW = False, Conversational = False, User = False, ACTION_FEATURE = False, SNAPSHOT_LEN = False):
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
        actions = sorted(actions, key=lambda k: k['timestamp_in_sec'])[::-1]
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
        actions = sorted(actions, key=lambda k: k['timestamp_in_sec'])[::-1]
        feature_set.update(_get_last_n_action_features(actions, 3, LEXICONS, ACTION_FEATURE))
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
        feature_set.update(_get_balance_features(actions))
        if not(assigned):
            for k in feature_set.keys():
                if not(k in colorcodes):
                    colorcodes[k] = color_cnt
        color_cnt += 1
        assiganed = True
        if SNAPSHOT_LEN:
            feature_set['snapshot_len'] = conversation['snapshot_len']
        conv_features.append((copy.deepcopy(feature_set), clss))
    participant_features = []
    starter_attack_profiles = {0: [], 1:[]}
    non_starter_attack_profiles = {0: [], 1: []}
    blocks = []
    user_info = []
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
        for k in feature_set.keys():
            if not(k in colorcodes):
                colorcodes[k] = color_cnt
        color_cnt += 1
        p, b = attacker_profile(conversation,  user_infos, feature_set, attacker_profile_ASPECTS)
        user_info.append(user_infos)
        if starter == ender:
            starter_attack_profiles[clss].append(p)
        else:
            non_starter_attack_profiles[clss].append(p)
        blocks.append(int(b))
        participant_features.append((copy.deepcopy(feature_set), clss))
    feature_sets = []

    for ind, pair in enumerate(documents):
        conversation, clss, conv_id = pair
        feature_set = {}
        if BOW:
            feature_set.update(bow_features[ind][0])
        if Conversational:
            feature_set.update(conv_features[ind][0])
        if User:
            feature_set.update(participant_features[ind][0])
        feature_sets.append((feature_set, clss))
    return user_info, starter_attack_profiles, non_starter_attack_profiles, feature_sets

print('Conversation')
user_info, starter_attack_profiles, non_starter_attacker_profiles, feature_sets= get_features(Conversational=True)
X, y, feature_names = documents2feature_vectors(feature_sets)
train_svm(X, y, 0.007, matched_pairs)

print('FULL')
user_info, starter_attack_profiles, non_starter_attacker_profiles, feature_sets = get_features(BOW=True, Conversational=True, User=True)
X, y, feature_names = documents2feature_vectors(feature_sets)
train_svm(X, y, 0.0009, matched_pairs)

print('BOW')
user_info, starter_attack_profiles, non_starter_attacker_profiles, feature_sets = get_features(BOW=True)
X, y, feature_names = documents2feature_vectors(feature_sets)
train_svm(X, y, 0.0007, matched_pairs)

print('User')
user_info, starter_attack_profiles, non_starter_attacker_profiles, feature_sets = get_features(User=True)
X, y, feature_names = documents2feature_vectors(feature_sets)
train_svm(X, y, 0.5, matched_pairs)

print('User + Conversation')
user_info, starter_attack_profiles, non_starter_attacker_profiles, feature_sets = get_features(User=True, Conversational=True)
X, y, feature_names = documents2feature_vectors(feature_sets)
train_svm(X, y, 0.007, matched_pairs)

print('BOW + Conversation')
user_info, starter_attack_profiles, non_starter_attacker_profiles, feature_sets = get_features(BOW=True, Conversational=True)
X, y, feature_names = documents2feature_vectors(feature_sets)
train_svm(X, y, 0.0007, matched_pairs)


