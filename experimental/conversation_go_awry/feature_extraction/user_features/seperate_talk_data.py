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

