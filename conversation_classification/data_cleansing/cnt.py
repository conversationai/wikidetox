import json

total = 0
for ind in range(70): 
    with open('/scratch/wiki_dumps/matched/data%d.json'%ind) as f: 
         for line in f:
             total += 1
print(total)

