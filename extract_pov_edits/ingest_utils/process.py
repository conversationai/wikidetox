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

COMPONENT_THERESHOLD = 10000
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


def format_clean(s):
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
  # mwparserfromhell clean.
  s = mwparserfromhell.parse(s).strip_code()
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


def process(content, cur_sents):
  """Main Processing Point."""
  sents = []
  error = False
  for component in split(format_clean(content['text'])):
    if len(component) < COMPONENT_THERESHOLD:
      # Prevents nltk from sentence tokenizing over-long paragraphs which might
      # result in endless execution and memory leak.
      sents.extend(nltk.sent_tokenize(component))
    else:
       error = True
  return diff(sents, cur_sents, content['rev_id']), error

