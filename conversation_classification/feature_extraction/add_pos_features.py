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

import nltk
import json

path = '/scratch/wiki_dumps/expr_with_matching/delta2_no_users/data/'
for data_file in ['test.json', 'train.json']:
    with open(path + data_file + '_new', 'w') as w:
         with open(path + data_file) as f:
             for line in f:
                 conv_id, clss, conversation = json.loads(line)
                 actions = conversation['action_feature']
                 new_actions = []
                 for action in actions:
                     action['pos_tags_with_words'] = nltk.pos_tag(action['unigrams'])
                     new_actions.append(action)
                 conversation['action_feature'] = new_actions
                 w.write(json.dumps([conv_id, clss, conversation]) + '\n')
         
