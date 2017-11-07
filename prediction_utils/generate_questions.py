import json

questions = []
constraints = ['delta2_no_users_attacker_in_conv'] # 'delta2_no_users', 
for constraint in constraints:
    with open('/scratch/wiki_dumps/expr_with_matching/%s/data/all_cleaned_2.json'%(constraint)) as f:
         for line in f:
             conv_id, clss, conversation = json.loads(line)
             end_time = max([a['timestamp_in_sec'] for a in conversation['action_feature']])
             for action in conversation['action_feature']:
                 if action['timestamp_in_sec'] == end_time:
                    continue
                 for ind, s in enumerate(action['sentences']):
                     if s[-1] == '?':
                        question = {'constraint' : constraint, \
		 		    'conversation_id' : conv_id, \
				    'action_id' : action['id'], \
                                    'sentence index' : ind, \
                                    'content' : s}
                        questions.append(question)  
#'/scratch/wiki_dumps/questions_altered.json'
with open('../../../yiqing_script/input.json', 'w') as w:
     json.dump(questions, w)
#     for question in questions:
#         w.write(json.dumps(question) + '\n')
