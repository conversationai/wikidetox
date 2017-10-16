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
        break

print(len(users.keys()))
print(users[list(users.keys())[0]])
