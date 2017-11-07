import json 

constraint = 'constraintA+B'

documents = []
conv_dict= {}
doc_dict = {}
ind_dict = {}
with open('/scratch/wiki_dumps/paired_conversations/%s/data/all.json'%(constraint)) as f:
    ind = 0
    for line in f:
        conv_id, clss, conversation = json.loads(line)
        actions = sorted(conversation['action_feature'], \
                key=lambda k: (k['timestamp_in_sec'], k['id'].split('.')[1], k['id'].split('.')[2]))
        doc_dict[conv_id] = (conversation, clss, conv_id)
        conv_dict[conv_id] = actions
        ind_dict[conv_id] = ind
        ind += 1
        documents.append((conversation, clss, conv_id)) 

doc_dic = {}
cnt = 0
max_gap = 0
max_l_gap = 0
deleted = {}
cleaned = []
feature_sets = []
altered = []
last_actions = {}
for ind, doc in enumerate(documents):
    conversation, clss, conv_id = doc
    actions = sorted(conversation['action_feature'], \
                key=lambda k: (k['timestamp_in_sec'], k['id'].split('.')[1], k['id'].split('.')[2]))
    conversation['action_feature'] = conversation['action_feature']
    end_time = max([a['timestamp_in_sec'] for a in actions])
    for a in actions:
        if a['timestamp_in_sec'] == end_time:
            last_actions[a['id']] = 1
    actions = [a for a in actions if a['timestamp_in_sec'] < end_time]
    if clss:
        matched_id = actions[0]['bad_conversation_id']
    else:
        matched_id = actions[0]['good_conversation_id']
        continue
    matched_l = len(conv_dict[matched_id])
    if len(actions) > matched_l:
        if actions[matched_l - 1]['timestamp_in_sec'] < actions[matched_l]['timestamp_in_sec'] \
           and 'user_text' in actions[matched_l] and \
            actions[matched_l]['user_text'] in [a['user_text'] for a in actions[:matched_l] if 'user_text' in a]:
            new_end_time = actions[matched_l]['timestamp_in_sec']
            actions = actions[:matched_l]
            conversation['action_feature'] = [a for a in conversation['action_feature'] if a['timestamp_in_sec'] <= new_end_time]
            altered.append((conv_id, clss, conversation))
    users = len(set([a['user_text'] if 'user_text' in a else None for a in actions]) - set([None]))
    users1 = len(set([a['user_text'] if 'user_text' in a else None for a in conv_dict[matched_id]]) - set([None]))
    if not(users == users1) or not(len(actions) == len(conv_dict[matched_id])):
        cnt += 1
        max_gap = max(max_gap, abs(users - users1))
        max_l_gap = max(max_l_gap, abs(len(conv_dict[matched_id]) - len(actions)))
    else:
        feature_sets.append(({'length': len(actions), 'no_users': users}, clss))
        feature_sets.append(({'length': len(conv_dict[matched_id]), 'no_users': users1}, 1-clss))
        cleaned.append((conversation, clss, conv_id))
        cleaned.append(doc_dict[matched_id])
    doc_dic[conv_id] = ind

with open('/scratch/wiki_dumps/paired_conversations/%s/data/clean.json'%(constraint), 'w') as w:
    for line in cleaned:
        conversation, clss, conv_id = line
        w.write(json.dumps((conv_id, clss, conversation)) + '\n')

