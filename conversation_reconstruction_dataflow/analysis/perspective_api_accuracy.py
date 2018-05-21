import json
import pandas as pd
import requests
import private

attributes = ['identity_hate', 'insult', 'obscene', 'threat']
#"toxicity","severe_toxicity","obscene", 
#def call_perspective_api(text):
#    path = ' https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze?key=%s' % PERSPECTIVE_KEY
#    request = {
#        'comment' : {'text' : text},
#        'spanAnnotations': True, 
#        'requestedAttributes' : {'TOXICITY_'+a.upper():{} for a in attributes},
#        'doNotStore' : True, 
#    }
#    response = requests.post(path, json=request)
#    prob = {}
#    if response.status_code == 429:
#       time.sleep(10)
#       return call_perspective_api(text) 
#    if response.status_code == 200:
#        data = json.loads(response.text)
#        scores_simplified = {}
#        attribute_scores = data['attributeScores']
#        for attr, data in attribute_scores.items(): 
#            prob[attr.lower()] = data['summaryScore']['value']
#        return prob
#    else:
#       return None
#
#with open("train.csv", "r") as f:
#     df = pd.read_csv(f, index_col=0)
##df['toxicity'] = df['toxic']
##df['severe_toxicity'] = df['severe_toxic']
#data = df.T.to_dict().values()
#labels = {a.lower():[] for a in attributes}
#scores = {a.lower():[] for a in attributes}
#length = len(df)
#cnt = 0
#for d in data:
#    score = call_perspective_api(d['comment_text'])
#    if score == None:
#       cnt += 1
#       continue
#    for l in labels:
#        labels[l].append(d[l]) 
#        scores[l].append(score['toxicity_'+l])
#    cnt += 1
#    if cnt % 500 == 0:
#       print("%d/%d finished."%(cnt, length))
#with open("tmp1.json", "w") as f:
#     f.write(json.dumps(labels) + '\n')
#     f.write(json.dumps(scores) + '\n')
eps = 1e-10

def compute_p_r(pred):
    true_positive = sum([int(arg[0] == arg[1] and arg[0] == 1) for arg in pred])
    false_positive = sum([int(arg[0] == 0 and arg[1] == 1) for arg in pred]) 
    false_negative = sum([int(arg[0] == 1 and arg[1] == 0) for arg in pred])  
    p = true_positive / (true_positive + false_positive)
    r = true_positive / (true_positive + false_negative)
    return p, r
         

def locate_err(labels, scores): 
    L = 0.
    R = 1.
    err = 0.5
    precision, recall = compute_p_r([(labels[ind], 1 if s > err else 0) for ind, s in enumerate(scores)])
    while L - R < -eps: 
          err = (L + R) / 2
          precision, recall = compute_p_r([(labels[ind], 1 if s > err else 0) for ind, s in enumerate(scores)])
          if recall - precision < -eps:
             R = err
          else:
             L = err
    print(precision, recall, err)
    return err

with open("tmp1.json", "r") as f:
     line1, line2 = f
     labels = json.loads(line1)
     scores = json.loads(line2)
for k in labels.keys():
    print(k, sum(labels[k]), len(labels[k]), sum(labels[k])/len(labels[k]))
err = {}
for a in attributes:
    print(a)
    err[a] = locate_err(labels[a], scores[a])

