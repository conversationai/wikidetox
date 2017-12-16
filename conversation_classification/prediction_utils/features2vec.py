import json
import pickle as cPickle
import numpy as np
from scipy.sparse import csr_matrix
import random
import matplotlib.pyplot as plt
from collections import defaultdict
from .user_features import attacker_profile, _user_features
from .bow_features import _get_term_features
from .utterance_features import _get_last_n_action_features, _get_action_features, _get_global_action_features
from .repeat_features import _get_repeatition_features
from .reply_features import _get_balance_features
import math
import re
import copy

def get_features(user_features, documents, ARGS, BOW = False, Conversational = False, User = False, SNAPSHOT_LEN = False, Questions = False, COMMENT_LEN = True):
    """
      Generates Features:
      Type of Features: 
          - BOW: bag of words features
          - Conversational: features extracted from the conversation
          - User: features based on participant information
          - SNAPSHOT_LEN: number of comments in the final snapshot
          - Questions: question features
          - COMMENT_LEN: number of comments added to the conversation 
    """
    STATUS, ASPECTS, attacker_profile_ASPECTS, LEXICONS, QUESTIONS, UNIGRAMS_LIST, BIGRAMS_LIST = ARGS 
    feature_sets = []
    # BOW features
    bow_features = []
    for pair in documents:
        conversation, clss, conv_id = pair
        feature_set = {}
        # exclude last action
        actions = conversation['action_feature']
        end_time = max([a['timestamp_in_sec'] for a in actions])
        actions = [a for a in actions if a['timestamp_in_sec'] < end_time]
        actions = sorted(actions, \
                key=lambda k: (k['timestamp_in_sec'], k['id'].split('.')[1], k['id'].split('.')[2]))[::-1]
        comments_actions = [a for a in actions if a['comment_type'] == 'SECTION_CREATION' or a['comment_type'] == 'COMMENT_ADDING']
        # update feature set
        feature_set.update(_get_term_features(comments_actions, UNIGRAMS_LIST, BIGRAMS_LIST))
        bow_features.append((copy.deepcopy(feature_set), clss))
    
    # Conversational featrues
    conv_features = []
    for pair in documents:
        conversation, clss, conv_id = pair
        feature_set = {}
        # exclude last action
        actions = conversation['action_feature']
        end_time = max([a['timestamp_in_sec'] for a in actions])
        actions = [a for a in actions if a['timestamp_in_sec'] < end_time]
        actions = sorted(actions, \
                key=lambda k: (k['timestamp_in_sec'], k['id'].split('.')[1], k['id'].split('.')[2]))[::-1]
        # only keep comment adding and section creation
        comments_actions = [a for a in actions if a['comment_type'] == 'SECTION_CREATION' or a['comment_type'] == 'COMMENT_ADDING']
        # conversational features from all actions that adds a comment 
        feature_set.update(_get_global_action_features(comments_actions))
        # conversational features from the last N actions that adds a comment
        feature_set.update(_get_last_n_action_features(comments_actions, 1, LEXICONS))
        # conversational features from the last action that adds a comment of each participant 
        feature_set.update(_get_action_features(comments_actions, LEXICONS))
        # conversational features based on a single participant's behavior in the conversation
        feature_set.update(_get_repeatition_features(comments_actions))
        # question features
        if Questions:
            feature_set.update(_get_question_features(conv_id, QUESTIONS))
        actions = actions[::-1]
        # conversational features based on reply relations 
        feature_set.update(_get_balance_features(actions))
        # number of comments in last snapshot
        if SNAPSHOT_LEN:
            feature_set['snapshot_len'] = conversation['snapshot_len']
        conv_features.append((copy.deepcopy(feature_set), clss))


    # pariticipant features
    # extract the last participant's profile
    participant_features = []
    starter_attack_profiles = {0: [], 1:[]}
    non_starter_attack_profiles = {0: [], 1: []}
    all_profiles = {0: [], 1: []}
    blocks = []
    user_info = []
    for ind, pair in enumerate(documents):
        conversation, clss, conv_id = pair
        # is the starter of the conversation also the last participant in the conversation
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
        feature_set, user_infos = _user_features(actions, user_features[conv_id], ASPECTS, STATUS)
        # last participant's profile
        p, b = attacker_profile(conversation,  user_infos, attacker_profile_ASPECTS)
        user_info.append(user_infos)
        if starter == ender:
            starter_attack_profiles[clss].append(p)
        else:
            non_starter_attack_profiles[clss].append(p)
        all_profiles[clss].append(p)
        # participants' block histories
        blocks.append(int(b))
        # update participant features
        participant_features.append((copy.deepcopy(feature_set), clss))
    feature_sets = []

    # update the returned feature set given the parameters
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
    return user_info, starter_attack_profiles, non_starter_attack_profiles, all_profiles, feature_sets

def _get_question_features(conv_id, QUESTIONS):
    """
      Given conversation id and a dictionary QUESTIONS
      Returns an one-hot vector of length 8, the Xth entry being 1 iff the conversation contains question type X.
    """
    ret = {}
    for ind in range(8):
        ret['question_type%d'%(ind)] = 0
    if conv_id in QUESTIONS:
        for x in QUESTIONS[conv_id]:
            ret['question_type%d'%(x)] = 1
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

