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
import pandas as pd
import csv
all_comments = []
cid = 0
mapping = {}
folder = 'last_comments_in_a_week'
total = {}
for ind in range(1, 71):
    with open('/scratch/wiki_dumps/expr_with_matching/%s/ForkPoolWorker-%d.json'%(folder, ind)) as f:
         for line in f:
             conv_id, comments = json.loads(line)
             #total.append([conv_id, comments])
             for user, c_lst in comments.items():
                 for c in c_lst:
                     all_comments.append(c) 
                     mapping[cid] = (conv_id, user)
                     cid += 1
print(len(all_comments))
with open('/scratch/wiki_dumps/expr_with_matching/%s/mapping.json'%(folder), 'w') as f:
     json.dump(mapping, f)

"""
folder = 'last_comments'
with open('/scratch/wiki_dumps/expr_with_matching/%s/all.json'%(folder), 'r') as f:
#     json.dump(total, f)
     comments = json.load(f)
"""
data = []
for ind, c in enumerate(comments):
    data.append({'comment': c, 'id': ind})
df = pd.DataFrame(data)
with open('/scratch/wiki_dumps/expr_with_matching/%s/comments_for_toxicity_scoring.csv'%(folder), 'w') as f:
    df.to_csv(f, encoding = 'utf-8', index=False, quoting=csv.QUOTE_ALL)
 
"""


#with open('/scratch/wiki_dumps/expr_with_matching/%s/mapping.json'%(folder), 'w') as f:
#     json.dump(mapping, f)

             total[conv_id] = user_features

with open('/scratch/wiki_dumps/expr_with_matching/user_features/updated.json') as f:
     all_features = json.load(f)
with open('/scratch/wiki_dumps/expr_with_matching/user_features/history_toxicity.json') as f:
     toxicity = json.load(f)

tox = {}
for pair in toxicity:
    conv_id, cur = pair
    tox[conv_id] = cur

updated = []
for pair in all_features:
    conv_id, user_features = pair
    for user in user_features.keys():
        if conv_id in tox and user in tox[conv_id]:
           user_features[user]['history_toxicity'] = tox[conv_id][user]
        else:
           user_features[user]['history_toxicity'] = 0
    updated.append((conv_id, user_features))
with open('/scratch/wiki_dumps/expr_with_matching/user_features/all.json', 'w') as f:
    json.dump(updated, f)

 

"""
