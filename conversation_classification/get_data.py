import json
from collections import defaultdict
import random


def get_data(constraint):
    all_conv = []
    for ind in range(70):
        with open('/scratch/wiki_dumps/expr_with_matching/%s/features/data%d.json'%ind) as f:
            for line in f:
                conv_id, conversation = json.loads(line)
                conv = conversation['action_feature'][0]
                if 'good_conversation_id' in conv:
                   clss = 0
                else:
                   clss = 1
                conversations[conv_id] = (conv_id, clss, conversation)
                if clss == 1:
                    all_conv.append((conv_id, conv['bad_conversation_id']))
    
    for c in all_conv:
        id1, id2 = c
        x = random.random()
        if x > 0.9:
           with open('/scratch/wiki_dumps/expr_with_matching/%s/data/test.json'%(constraint), 'a') as f:
                f.write(json.dumps(conversations[id1]) + '\n')
                f.write(json.dumps(conversations[id2]) + '\n')
        else:
           if x > 0.8:
               with open('/scratch/wiki_dumps/expr_with_matching/%s/data/develop.json'%(constraint), 'a') as f:
                   f.write(json.dumps(conversations[id1]) + '\n')
                   f.write(json.dumps(conversations[id2]) + '\n')
           else:
               with open('/scratch/wiki_dumps/expr_with_matching/%s/data/train.json'%(constraint), 'a') as f:
                   f.write(json.dumps(conversations[id1]) + '\n')
                   f.write(json.dumps(conversations[id2]) + '\n')
     
     
