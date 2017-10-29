import json

questions = []
constraints = ['delta2_no_users', 'delta2_no_users_attacker_in_conv']
for constraint in constraints:
    with open('/scratch/wiki_dumps/expr_with_matching/%s/data/all.json'%(constraint)) as f:
         for line in f:
             conv_id, clss, conversation = json.loads(line)
             for action in conversation['action_feature']:
                 for ind, s in enumerate(action['sentences']):
                     if s[-1] == '?':
                        question = {'constraint' : constraint, \
		 		    'conversation_id' : conv_id, \
				    'action_id' : action['id'], \
                                    'sentence index' : ind, \
                                    'content' : s}
                        questions.append(question)  
with open('/scratch/wiki_dumps/questions.json', 'w') as w:
     for question in questions:
         w.write(json.dumps(question) + '\n')
