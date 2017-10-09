from conversation_constructor import Conversation_Constructor
import json
import fileinput
import sys

def reconstruct(page_history):
    processor = Conversation_Constructor(COMMENT_TRACKING_FILE = "comments.json")
    actions_lst = []
    sys.stderr.write(page_history[0]['page_title'])
    for ind, h in enumerate(page_history):
#        print(h['page_title'])
#        print(list(h.keys()))
        actions = processor.process(h, DEBUGGING_MODE = False)
        for action in actions:
            print(json.dumps(action))

with open("/scratch/wiki_dumps/history10-p2371146p2406006.json", "r") as f:
    for line in f: 
       page_history = json.loads(line)
       reconstruct(page_history) 
