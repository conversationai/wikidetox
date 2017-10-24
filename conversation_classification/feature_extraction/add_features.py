import nltk
import json

path = '/scratch/wiki_dumps/expr_with_matching/delta2_no_users/data/'
for data_file in ['test_verified.json', 'train_verified.json']:
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
         
