import pandas as pd
from collections import defaultdict
import os

users = defaultdict(list)

for year in range(2001, 2016):
    df = pd.read_csv('/scratch/wiki_dumps/user_data/talk_data/activity_article_%d.csv'%year, sep="\t")
    user_groups = df.groupby(['user_text'])
    for user, data in user_groups:
        users[user].append(data)
    print(year)

for user in users.keys():
    with open("/scratch/wiki_dumps/user_data/talk_per_user/%s"%user, "w") as w:
         users[user] = pd.concat(users[user])
         users[user].to_csv(w, sep="\t")

