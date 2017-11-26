import json
import pickle as cPickle
import numpy as np
from collections import defaultdict
import os
import csv
import datetime
import pandas as pd
import requests
import re

def get_activity_cnt(ns, year):

    users = set([])
    os.system('tar -xzf /scratch/wiki_dumps/wikipedia_talk_corpus/comments_%s_%d.tar.gz' % (ns, year))
    data_dir = "comments_%s_%d" % (ns, year)
    total = []
    for _, _, filenames in os.walk(data_dir):
        for filename in filenames:
            if re.match("chunk_\d*.tsv", filename):
                df = pd.read_csv(os.path.join(data_dir, filename), sep = "\t")
                df = df[df['user_text'].isin(usrlst)]
                total.append(df)
    ret = pd.concat(total)
    os.system('rm -r comments_%s_%d' % (ns, year))
    return ret

users = {}
user_id = {}
constraints = ['delta2_no_users', 'delta2_no_users_attacker_in_conv']
for constraint in constraints:
    with open('/scratch/wiki_dumps/expr_with_matching/%s/data/all.json'%(constraint)) as f:
        for line in f:
            conv_id, clss, conversation = json.loads(line)
            for action in conversation['action_feature']:
                if 'user_text' in action:
                    users[action['user_text']] = []       
                    if 'user_id' in action:
                       user_id[action['user_text']] = action['user_id']
                    else:
                       user_id[action['user_text']] = '0|'+ action['user_text']
usrlst = list(users.keys())
print('usrlst generated')

for year in range(2001, 2016):
    activity = []
    for ns in ['article', 'user']:
        act = get_activity_cnt(ns, year)
        print(year, ns, len(act))
        with open("/scratch/wiki_dumps/user_data/talk_data/activity_%s_%d.csv"%(ns, year), "w") as f:
            act.to_csv(f, sep="\t", encoding='utf-8', index=None)

