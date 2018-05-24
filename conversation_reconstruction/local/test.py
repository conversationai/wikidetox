from conversation_constructor import Conversation_Constructor
import json
import fileinput
import sys

with open("/scratch/wiki_dumps/history10-p2371146p2406006.json", "r") as f:
    for line in f: 
       page_history = json.loads(line)
       for rev in page_history:
          if not('rev_id' in rev and 'user_id' in rev and 'user_text' in rev and 'timestamp' in rev and 'page_id' in rev and 'page_title' in rev):
             print(rev)
