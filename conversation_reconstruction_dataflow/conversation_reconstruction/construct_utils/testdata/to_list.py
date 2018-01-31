import json
data = {}
data['table'] = "wikidetox_conversations.test_page_2_issue24"
filename = "downloaded"
data['weeks'] = []
with open(filename) as f:
     for line in f: 
         d= json.loads(line)         
         data['weeks'].append(d)
with open('test_revisions_list.json', 'w') as w:
     json.dump(data, w)
