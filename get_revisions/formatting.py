import fileinput
import json

for line in fileinput.input():
    content = json.loads(line)
    page = []
    for rev in content['revisions']:
        rev['page_id'] = content['page_id']
        rev['page_title'] = content['page_title']
        rev['page_namespace'] = content['page_namespace']
        page.append(rev)
    if '/Archive' in content['page_title']:
        # Archived talk pages should be stored somewhere else but instead of  
        # going through the conversation reconstruction process. 
        pass
    else:
        print(json.dumps(page)) 
