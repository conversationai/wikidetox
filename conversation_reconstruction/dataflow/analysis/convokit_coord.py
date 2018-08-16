"""
This is a file using convokit to compute coordination.
"""

import json
import argparse
import convokit

parser = argparse.ArgumentParser()
parser.add_argument('--input',
                    dest='input')
known_args, _ = parser.parse_known_args()
corpus = convokit.Corpus(filename=known_args.input)
coord = convokit.Coordination(corpus)
group_A = corpus.users(lambda user: user.info["owner"])
group_A = corpus.users(lambda user: not(user.info["owner"]))
scores = coord.score(group_A, group_B)
average_by_marker_agg1, average_by_marker, agg1, agg2, agg3 = coord.score_report(scores)
print(average_by_marker_agg1, average_by_marker, agg1, agg2, agg3)

