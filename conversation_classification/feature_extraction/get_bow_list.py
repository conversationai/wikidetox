import json
from collections import defaultdict
import pickle as cPickle
import os

def generate_bow_features(constraint, documents):
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
    for uni_min in [10, 15, 20, 50, 100]:
        unigram_features = list(filter(lambda x: unigram_counts[x] > uni_min, unigram_counts.keys()))
        print(len(unigram_features))
        cPickle.dump(unigram_features, open('/scratch/wiki_dumps/expr_with_matching/%s/bow_features/unigram%d.pkl'%(constraint, uni_min), 'wb'))
    for bi_min in [10, 20, 50, 100, 500]:
        bigram_features = list(filter(lambda x: bigram_counts[x] > bi_min, bigram_counts.keys()))
        print(len(bigram_features))
        cPickle.dump(bigram_features, open('/scratch/wiki_dumps/expr_with_matching/%s/bow_features/bigram%d.pkl'%(constraint, bi_min), 'wb'))
   
def process(constraint):
    documents = []
    with open('/scratch/wiki_dumps/expr_with_matching/%s/data/train.json'%(constraint)) as f:
        for line in f:
            conv_id, clss, conversation = json.loads(line)
            documents.append((conversation, clss))       
    generate_bow_features(constraint, documents)


constraints = ['delta2_none', 'delta2_no_users', 'delta3_none', 'delta3_no_users']
#['delta2_no_users_attacker_in_conv']
#['delta2_attacker_in_conv',  'delta3_attacker_in_conv', 'delta3_no_users_attacker_in_conv']
for c in constraints:
    os.system('mkdir /scratch/wiki_dumps/expr_with_matching/%s/bow_features/'%(c))
    process(c)
    print(c)


