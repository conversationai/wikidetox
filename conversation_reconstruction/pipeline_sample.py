from conversation_constructor import Conversation_Constructor
import json
import fileinput

def reconstruct(page_history):
    processor = Conversation_Constructor(COMMENT_TRACKING_FILE = "comments.json")
    actions_lst = []
    for ind, h in enumerate(page_history):
        actions = processor.process(h, DEBUGGING_MODE = False)
        for action in actions:
            print(json.dumps(action))

with open("/scratch/wiki_dumps/history10-p2371146p2406006.json", "r") as f:
    for line in f: 
       page_history = json.loads(line)
       reconstruct(page_history) 
