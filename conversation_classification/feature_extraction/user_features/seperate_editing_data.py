import pandas as pd
from collections import defaultdict
import os

edits = []
data_dir = "/scratch/wiki_dumps/user_data/editing_data/"
users = defaultdict(list)
for _, _, filenames in os.walk(data_dir):
    for filename in filenames:
        df = pd.read_csv(os.path.join(data_dir, filename))
        user_groups = df.groupby(['user'])
        for user, data in user_groups:
            users[user].append(data)
        print(filename)

for user in users.keys():
    with open("/scratch/wiki_dumps/user_data/editing_per_user/%s"%user, "w") as w:
         users[user] = pd.concat(users[user])
         users[user].to_csv(w)

