from .conversation_reconstruction.conversation_constructor import Conversation_Constructor
import json
import fileinput

def reconstruct(page_history):
    processor = Conversation_Constructor(COMMENT_TRACKING_FILE = "comments.json")
    actions_lst = []
    start = time.time()
    for ind, h in enumerate(page_history):
        actions = processor.process(h, DEBUGGING_MODE = False)
        for action in actions:
            print(json.dumps(action))

for line in fileinput.input():
    page_history = json.loads(line)
    reconstruct(page_history) 
