"""
Copyright 2018 Google Inc.
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

-------------------------------------------------------------------------------

Process Edits

Computes diff between Wikipedia revisions at sentence level and extracts POV rejects.

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


import re
import nltk
import mwparserfromhell
import multiprocessing
from nltk import word_tokenize

SENTENCE_THERESHOLD = 3
MATCHING_THERESHOLD = 0.6
COMPONENT_THERESHOLD = 10000
SIZE_DIFF_THERESHOLD = 100
TIMEOUT = 2
CONTEXT_RANGE = 3


def change_close_by(CONTEXT_RANGE, ind, changes):
  length = len(changes) - 1
  for inc in range(1, CONTEXT_RANGE+1):
    if inc + ind < length and changes[inc + ind]:
      return True
    if ind - inc >= 0 and changes[ind - inc]:
      return True
  return False


def diff(sents, cur_sents, rev_id):
  """Computes diff at sentence level."""
  sents_old = cur_sents.keys()
  new_seq = {}
  equals = []
  inserts = []
  deletes = []
  change_in_new = []
  for s in sents:
    if s in sents_old:
      new_seq[s] = cur_sents[s]
      equals.append((s, cur_sents[s]))
      change_in_new.append(False)
    else:
      new_seq[s] = rev_id
      inserts.append((s, rev_id))
      change_in_new.append(True)
  change_in_old = []
  for s in sents_old:
    if s not in sents:
      change_in_old.append(True)
      deletes.append((s, cur_sents[s]))
    else:
      change_in_old.append(False)
  # Locate context sentences that are unchanged near the inseted/deleted
  # sentences.
  context_equals = set()
  for ind, s in enumerate(sents):
    if (not change_in_new[ind] and
        change_close_by(CONTEXT_RANGE, ind, change_in_new)):
        context_equals.add(s)
  for ind, s in enumerate(sents_old):
    if (not change_in_old[ind] and
        change_close_by(CONTEXT_RANGE, ind, change_in_old)):
        context_equals.add(s)
  # Dedeuplicate sentences.
  context_equals = list(context_equals)
  return context_equals, inserts, deletes, new_seq


def diff_pair(sents, sents_old):
  """Computes diff at sentence level."""
  equals = []
  inserts = []
  deletes = []
  change_in_new = []
  for s in sents:
    if s in sents_old:
      equals.append(s)
      change_in_new.append(False)
    else:
      inserts.append(s)
      change_in_new.append(True)
  change_in_old = []
  for s in sents_old:
    if s not in sents:
      change_in_old.append(True)
      deletes.append(s)
    else:
      change_in_old.append(False)
  # Locate context sentences that are unchanged near the inseted/deleted
  # sentences.
  context_equals = set()
  for ind, s in enumerate(sents):
    if (not change_in_new[ind] and
        change_close_by(CONTEXT_RANGE, ind, change_in_new)):
        context_equals.add(s)
  for ind, s in enumerate(sents_old):
    if (not change_in_old[ind] and
        change_close_by(CONTEXT_RANGE, ind, change_in_old)):
        context_equals.add(s)
  # Dedeuplicate sentences.
  context_equals = list(context_equals)
  return context_equals, inserts, deletes


def format_clean(s, error):
  """Clean MediaWiki format."""
  # Clean titles
  ret = []
  for line in s.splitlines():
    front_cnt = re.search("^=+", line)
    back_cnt = re.search("^=+", line[::-1])
    if (front_cnt is None or back_cnt is None
        or len(front_cnt.group(0)) != len(back_cnt.group(0))):
      ret.append(line)
  s = "\n".join(ret)
  try:
     # mwparserfromhell clean.
     s = mwparserfromhell.parse(s).strip_code()
  except:
     error = True
     pass
  return s


def split(text):
  """Split the paragraph using !?. and line break."""
  sentence_break = '!?.\n'
  length = len(text)
  start = 0
  for ind, ch in enumerate(text):
    if (ind == length - 1) or (ch in sentence_break
                               and (text[ind + 1] not in sentence_break)):
       ret = text[start:ind + 1].strip()
       if ret:
          yield ret
       start = ind + 1


def _process(args):
  """Dry run to test if the revision will break the pipeline."""
  (content, cur_sents, error) = args
  sents = []
  for component in split(format_clean(content['text'], error)):
    if len(component) < COMPONENT_THERESHOLD:
      # Prevents nltk from sentence tokenizing over-long paragraphs which might
      # result in endless execution and memory leak.
      sents.extend(nltk.sent_tokenize(component))
  try:
     _ = diff(sents, cur_sents, content['rev_id'])
  except KeyError:
    error = True


def process(content, cur_sents):
  """Main Processing Point."""
  error = False
  p = multiprocessing.Process(target = _process, name = "subprocess",
                              args=((content, cur_sents, error), ))
  p.start()
  p.join(TIMEOUT)
  if p.is_alive() or error:
    error = True
    p.terminate()
    p.join()
    return diff(cur_sents, cur_sents, content['rev_id']), True
  sents = []
  error = False
  for component in split(format_clean(content['text'], error)):
    if len(component) < COMPONENT_THERESHOLD:
      # Prevents nltk from sentence tokenizing over-long paragraphs which might
      # result in endless execution and memory leak.
      sents.extend(nltk.sent_tokenize(component))
    else:
       error = True
  return diff(sents, cur_sents, content['rev_id']), error


def matched(sent1, sent2):
  tokens1 = word_tokenize(sent1)
  tokens2 = word_tokenize(sent2)
  overlapping_rate1 = len(set(tokens1)&set(tokens2))/float(len(set(tokens1)))
  overlapping_rate2 = len(set(tokens1)&set(tokens2))/float(len(set(tokens2)))
  return (sent1 != sent2 and
          len(tokens1) >= SENTENCE_THERESHOLD and
          overlapping_rate1 >= MATCHING_THERESHOLD and
          overlapping_rate2 >= MATCHING_THERESHOLD)


def process_pair(former, content):
  """Main Processing Point for Revision Pairs."""
  error = False
  if former:
    former_sents = nltk.sent_tokenize(format_clean(former['text'], error))
  else:
    former_sents = []
  sents = nltk.sent_tokenize(format_clean(content['text'], error))
  context_equal, inserts, deletes = diff_pair(sents, former_sents)
  sentence_revises = []
  for sent1 in inserts:
    for sent2 in deletes:
      if matched(sent1, sent2):
        sentence_revises.append((sent2, sent1))
  return context_equal, inserts, deletes, sentence_revises

def isSimilar(former, content):
  # Compare revision size
  if former == None:
    return False
  size_former = len(former['text'])
  size_content = len(content['text'])
  print(size_former, size_content)
  return (max(size_former, size_content) - min(size_former, size_content) < SIZE_DIFF_THERESHOLD)
