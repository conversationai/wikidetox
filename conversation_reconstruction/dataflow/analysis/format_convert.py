"""
This is a file converting the data into the right format for convokit.
"""

import json
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--output',
                    dest='output')
parser.add_argument('--input',
                    dest='input')

known_args, _ = parser.parse_known_args()
allInput = []
with open(known_args.input, "r") as f:
  for line in f:
    data = json.loads(line)
    convokitInput = {"id": data["id"], "root": data["replyTo_ancestor_id"], "reply-to": data["replyTo_ancestor_id"],
                     "text": data["content"], "timestamp":data["timestamp"], "user": data["user_text"],
                     "user-info": {"owner": True}}
    allInput.append(convokitInput)
    convokitInput = {"id": data["replyTo_ancestor_id"], "root": data["replyTo_ancestor_id"],
                     "text": data["replyTo_content"], "timestamp": None, "user": data["replyTo_user"],
                     "user-info": {"owner": False}}
    allInput.append(convokitInput)


with open(known_args.output, "w") as w:
  json.dump(allInput, w)
