import json
from collections import defaultdict
cats = [10, 12, 18, 16, 3, 9, 17, 20]
dat = defaultdict(list)
cnts = 0
with open("data/LIWC2007_English080730.dic", "r") as f:
     for line in f:
         data = line.split()
         word = data[0]
         if word[-1] == "*": word = word[:-1]
         wc = [int(d) for d in data[1:]]
         for c in cats:
             if c in wc:
               dat[word].append(c)
               cnts += 1
with open("data/liwc.json", "w") as f:
     json.dump(dat, f)
