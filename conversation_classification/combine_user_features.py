import json
"""
all_comments = []
cid = 0
mapping = {}
folder = 'user_features' #'last_comments'
total = []
for ind in range(1, 71):
    with open('/scratch/wiki_dumps/expr_with_matching/%s/ForkPoolWorker-%d.json'%(folder, ind)) as f:
         for line in f:
             conv_id, comments = json.loads(line)
             total.append([conv_id, comments])
             for user, c_lst in comments.items():
                 for c in c_lst:
                     all_comments.append(c) 
                     mapping[cid] = (conv_id, user)
                     cid += 1
print(len(all_comments))
"""

folder = 'last_comments'
with open('/scratch/wiki_dumps/expr_with_matching/%s/all.json'%(folder), 'r') as f:
#     json.dump(total, f)
     comments = json.load(f)
with open('/scratch/wiki_dumps/expr_with_matching/%s/comments.json'%(folder), 'w') as f:
#     json.dump(total, f)
     for c in comments:
         f.write(json.dumps(c) + '\n')



#with open('/scratch/wiki_dumps/expr_with_matching/%s/mapping.json'%(folder), 'w') as f:
#     json.dump(mapping, f)


