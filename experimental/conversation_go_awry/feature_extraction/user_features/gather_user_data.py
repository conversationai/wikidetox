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
import pickle as cPickle
import numpy as np
from collections import defaultdict
import os
import csv
import datetime
from multiprocessing import Pool
import pandas as pd

with open('/scratch/wiki_dumps/user_data.json', 'r') as w:
    users_of_interest = json.load(w)

users_edit_history = defaultdict(list)


def process(fname):
    with open(rootDir+'/'+fname, 'r') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',')
        firstline = True
        for row in csvreader:
            if firstline:
                firstline = False
            else:
                page_id, rev_id, timestamp, editor = row
                timestamp_in_sec =  (datetime.datetime.strptime(timestamp[:-3], '%Y-%m-%d %H:%M:%S') \
                                     -datetime.datetime(1970,1,1)).total_seconds()\
                                    + 60 * 60 * int(timestamp[-2:])
                data.append({'page_id': page_id, 'rev_id': rev_id, 'timestamp': timestamp, 'user': editor, 'timestamp_in_sec': timestamp_in_sec})
    df= pd.DataFrame(data)
    df = df[df['user'].isin(users_of_interest)]
    df.to_csv('/scratch/wiki_dumps/user_data/%s.csv'%(fname), encoding = 'utf-8', index=False, quoting=csv.QUOTE_ALL)
    print(fname)

rootDir = '/scratch/wiki_dumps/revisions'
plst = []
for dirName, subdirList, fileList in os.walk(rootDir):
    data = []
    for fname in fileList:
        plst.append(fname)
print(len(plst))
pool = Pool(30)
pool.map(process, plst)
