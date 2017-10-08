import fileinput
import json

for line in fileinput.input():
    content = json.loads(line)
    if int(content["page-namespace"]) in [1, 3, 5, 7, 9, 11, 13, 15]: 
       print(line) 
