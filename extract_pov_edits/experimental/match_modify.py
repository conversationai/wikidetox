"""
Matching deleted sentences with the revised version of it (if any) in Wikipedia edits.
Input:
  rejected.json -- Sentences deleted in revisions.
  improved.json -- Sentences added in the same set of revisions.
Constraint:
  1. Every revision in rejected.json appears exactly once.
  2. Every revision appeared in rejected.json matches with one or more revisions in improved.json.
Output:
  Revised sentences with metadata.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
from nltk import word_tokenize

SENTENCE_THERESHOLD = 3
MATCHING_THERESHOLD = 0.6

def read_data(filename):
  ret = []
  with open("data/%s.json" % filename, "r") as f:
    for line in f:
      input_data = json.loads(line)
      # Fix data formats.
      data = {key[2:] : val for key, val in input_data.iteritems()}
      data['rev_id'] = int(data['rev_id'])
      ret.append(data)
  return ret

def matched(sent1, sent2):
  tokens1 = word_tokenize(sent1)
  tokens2 = word_tokenize(sent2)
  overlapping_rate1 = len(set(tokens1)&set(tokens2))/float(len(set(tokens1)))
  overlapping_rate2 = len(set(tokens1)&set(tokens2))/float(len(set(tokens2)))
  return (sent1 != sent2 and
          len(tokens1) >= SENTENCE_THERESHOLD and
          overlapping_rate1 >= MATCHING_THERESHOLD and
          overlapping_rate2 >= MATCHING_THERESHOLD)


if __name__ == '__main__':
  improved = read_data('improved')
  improved = sorted(improved, key = lambda x: x['rev_id'])
  rejected = read_data('rejected')
  rejected = sorted(rejected, key = lambda x: x['rev_id'])
  i_ind = 0
  length = len(improved)
  improvements = []
  for r_ind, r in enumerate(rejected):
    sentences = []
    while i_ind < length and improved[i_ind]['rev_id'] == r['rev_id']:
      sentences.append(improved[i_ind]['content'])
      i_ind += 1
    cnt = 0
    for sent in sentences:
      if matched(r['content'], sent):
        r['improved_content'] = sent
        improvements.append(r)
        cnt += 1
  with open("data/improvements.json", "w") as f:
    for line in improvements:
      f.write(json.dumps(line) + '\n')



