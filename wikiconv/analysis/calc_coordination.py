import json
import nltk
import time
from collections import defaultdict

markers = [10, 12, 18, 16, 3, 9, 17, 20]
# categories in LIWC selected as markers to compute coordination value

def get_words(content):
    words = [liwc[w.lower()] for w in nltk.word_tokenize(content) if w.lower() in liwc]
    ret = {m: 0 for m in markers}
    for w in words:
        for m in w:
            ret[m] = 1
    return ret

def load_liwc():
   with open("data/liwc.json", "r") as f:
        liwc = json.load(f)
   return liwc

liwc = load_liwc()
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
              data.update(ret)
              w.write(json.dumps(data) + "\n")
              if (cnt % 500 == 0):
                 print("%f: %d/3658617 finished"%(time.time() - start, cnt))

