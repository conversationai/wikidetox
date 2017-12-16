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
from collections import defaultdict
import csv
import numpy as np
folder = 'last_comments'

with open('/scratch/wiki_dumps/expr_with_matching/%s/mapping.json'%(folder)) as f:
     mapping = json.load(f)
history_toxicity = {}
for ind in range(13):
    with open('/scratch/wiki_dumps/toxicity_scores/toxicity_scored_0%02d.csv'%(ind)) as f:
         df = pd.read_csv(f, encoding = 'utf-8', index_col=None, quoting=csv.QUOTE_ALL)
    print(ind, len(df))
    for index, row in df.iterrows():
        conv_id, user = mapping[str(row['id'])] 
        if not(conv_id in history_toxicity):
           history_toxicity[conv_id] = defaultdict(list)
        history_toxicity[conv_id][user].append(row['TOXICITY'])
    print(ind, 'finished')
output = []
for conv_id, conv  in history_toxicity.items():
    out = {}
    for user, toxicity in conv.items():
        out[user] = np.mean(toxicity)
    output.append((conv_id, out))

with open('/scratch/wiki_dumps/expr_with_matching/user_features/history_toxicity.json', 'w') as w:
     json.dump(output, w)


