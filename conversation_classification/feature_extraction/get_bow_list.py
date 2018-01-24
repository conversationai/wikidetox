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
from collections import defaultdict
import pickle as cPickle
import os

def generate_bow_features(constraint, documents, suffix):
    unigram_counts, bigram_counts = defaultdict(int), defaultdict(int)

    for pair in documents:
        conversation, clss = pair
        actions = conversation['action_feature']
        unigrams = set([])
        bigrams = set([])
        end_time = 0
        for action in actions:
            if action['timestamp_in_sec'] > end_time:
               end_time = action['timestamp_in_sec'] 
        for action in actions:
            if action['timestamp_in_sec'] == end_time or \
               not(action['comment_type'] == 'COMMENT_ADDING' or\
                   action['comment_type'] == 'SECTION_CREATION' or\
                   action['comment_type'] == 'COMMENT_MODIFICATION'):
               continue
            unigrams = unigrams | set(action['unigrams']) 
            bigrams = bigrams | set([tuple(x) for x in action['bigrams']])
        for w in unigrams: unigram_counts[w] += 1
        for w in bigrams: bigram_counts[w] += 1
    print(len((unigram_counts.keys())))
    print(len((bigram_counts.keys())))
    for uni_min in [15, 20, 50, 100, 150]:
        unigram_features = list(filter(lambda x: unigram_counts[x] > uni_min, unigram_counts.keys()))
        print(len(unigram_features))
        cPickle.dump(unigram_features, open('/scratch/wiki_dumps/expr_with_matching/%s/bow_features/unigram%d%s.pkl'%(constraint, uni_min, suffix), 'wb'))
    for bi_min in [10, 20, 50, 100, 200]:
        bigram_features = list(filter(lambda x: bigram_counts[x] > bi_min, bigram_counts.keys()))
        print(len(bigram_features))
        cPickle.dump(bigram_features, open('/scratch/wiki_dumps/expr_with_matching/%s/bow_features/bigram%d%s.pkl'%(constraint, bi_min, suffix), 'wb'))
   
def process(constraint, suffix):
    documents = []
    with open('/scratch/wiki_dumps/expr_with_matching/%s/data/all%s.json'%(constraint, suffix)) as f:
        for line in f:
            conv_id, clss, conversation = json.loads(line)
            documents.append((conversation, clss))       
    generate_bow_features(constraint, documents, suffix)


constraints =['delta2_no_users_attacker_in_conv'] # 
#['delta2_none', 'delta2_no_users', 'delta3_none', 'delta3_no_users']
#['delta2_no_users_attacker_in_conv']
#['delta2_attacker_in_conv',  'delta3_attacker_in_conv', 'delta3_no_users_attacker_in_conv']
suffix = '_cleaned_3'
for c in constraints:
    os.system('mkdir /scratch/wiki_dumps/expr_with_matching/%s/bow_features/'%(c))
    process(c, suffix)
    print(c)


