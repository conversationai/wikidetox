from __future__ import absolute_import, division, print_function
from builtins import *
from future.builtins.disabled import *

from .conversation_constructor import Conversation_Constructor
import json
import fileinput
import sys

class ConstructingPipeline():
    def __init__(self, page_history, output_file):
        self.page_history = page_history
        self.output_file = output_file

    def reconstruct(content):
        page_history = []
        for rev in content['revisions']:
            rev['page_id'] = content['page_id']
            rev['page_title'] = content['page_title']
            rev['page_namespace'] = content['page_namespace']
            page_history.append(rev)
        processor = Conversation_Constructor(COMMENT_TRACKING_FILE = "comments.json")
        actions_lst = []
        for ind, h in enumerate(page_history):
            actions = processor.process(h, DEBUGGING_MODE = False)
            for action in actions:
                print(json.dumps(action) + '\n')

    def run_constructor(self):
        with open(self.output_file, "w") as w:
            reconstruct(page_history)
