import json
import nltk
import time
from collections import defaultdict

def get_words(content):
    words = [liwc[w.lower()] for w in nltk.word_tokenize(content) if w.lower() in liwc]
    ret = {m: 0 for m in markers}
    for w in words:
        for m in w:
            ret[m] = 1
    return ret
 

markers = [10, 12, 18, 16, 3, 9, 17, 20]
with open("data/liwc.json", "r") as f:
     liwc = json.load(f)

coordination = defaultdict(list)
utterances = defaultdict(int)
target_and_speaker = {m: defaultdict(int) for m in markers}
speaker = {m: defaultdict(int) for m in markers}
target = {m: defaultdict(int) for m in markers}
filename = "data/own_page.json"
cnt = 0
start = time.time()
with open("data/own_page_coord.json", "w") as w:
     with open(filename, "r") as f:
          for line in f:
              cnt += 1
              data = json.loads(line)
              user = data['user_text']
              content = get_words(data["content"])
              if cnt == 1157357 or cnt == 2973467:
                 data['replyTo_content'] = "Hey dude"
              if cnt == 3140491 or cnt == 2578020:
                 data['replyTo_content'] = ""
              replyTocontent = get_words(data["replyTo_content"])
              ret = {}
              for m in markers: 
                  t = replyTocontent[m]
                  s = content[m] 
                  ret[m] = (t, s)
                  #ts = int(t and s) 
                  #target_and_speaker[m][user] += ts
                  #target[m][user] += t
                  #speaker[m][user] += s
              #utterances[user] += 1
              data.update(ret)
              w.write(json.dumps(data) + "\n")
              if (cnt % 500 == 0):
                 print("%f: %d/3658617 finished"%(time.time() - start, cnt))

#with open("tmp-2500000-3000000.json", "w") as w:
#     w.write(json.dumps(utterances) + "\n")
#     w.write(json.dumps(target_and_speaker) + "\n")
#     w.write(json.dumps(speaker) + "\n")
#     w.write(json.dumps(target) + "\n")

#for user in utterances.keys():
#    for m in markers:
#        try:
#            tmp = target_and_speaker[m][user] / target[m][user] - speaker[m][user] / utterances[user]
#        except:
#            tmp = None
#        coordination[m].append(tmp)
#with open("coordination_on_others.json", "w") as w:
#     json.dump(coordination, w)
