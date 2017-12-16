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

def _get_term_features(actions, UNIGRAMS_LIST, BIGRAMS_LIST):
    """
      Given the list of unigrams and bigrams
      returns the BOW feature vectors
    """
    unigrams, bigrams = set([]), set([])
    f = {}
    for action in actions:
        unigrams = unigrams | set(action['unigrams'])
        bigrams = bigrams | set([tuple(x) for x in action['bigrams']]) 
    f.update(dict(map(lambda x: ("UNIGRAM_" + str(x), 1 if x in unigrams else 0), UNIGRAMS_LIST)))
    f.update(dict(map(lambda x: ("BIGRAM_" + str(x), 1 if tuple(x) in bigrams else 0), BIGRAMS_LIST)))
    return f 


