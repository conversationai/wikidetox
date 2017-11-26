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


