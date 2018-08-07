"""This is not a google3 package.

Before running:
  pip install mwparserfromhell
  pip instlal nltk
  python -m nltk.downloader "punkt"
"""


import argparse
from collections import defaultdict
import json
import logging
import os
import re
import mwparserfromhell
from nltk.tokenize import sent_tokenize

CONTEXT_RANGE = 3

def change_close_by(CONTEXT_RANGE, ind, changes):
  length = len(changes) - 1
  for inc in range(1, CONTEXT_RANGE+1):
    if inc + ind < length and changes[inc + ind]:
      return True
    if ind - inc and changes[ind - inc]:
      return True
  return False


def diff(sents, cur_sents, rev_id):
  """Computes diff at sentence level."""
  sents_old = [s for s in cur_sents.keys()]
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
  context_equals = []
  for ind, s in enumerate(sents):
    if (not change_in_new[ind] and
        change_close_by(CONTEXT_RANGE, ind, change_in_new)):
        context_equals.append(s)
  for ind, s in enumerate(sents_old):
    if (not change_in_old[ind] and
        change_close_by(CONTEXT_RANGE, ind, change_in_old)):
        context_equals.append(s)
  # Dedeuplicate sentences.
  context_equals = list(set(context_equals))
  return context_equals, inserts, deletes, new_seq


def format_clean(s):
  """Clean MediaWiki format."""
  # Clean titles.
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

def run(args):
  """Main entry point."""
  path = os.path.join(args.input_path, "test")
  revisions = [f for f in os.listdir(path)
               if os.path.isfile(os.path.join(path, f))]
  rev_ids = sorted([int(re.search(r"(?<=revision_)\d*", r).group(0))
                    for r in revisions if re.search(r"(?<=revision_)\d*", r)])
  authors = {}
  cur_sents = {}
  pov_sents = []
  npov_sents = []
  author_pov_revs = defaultdict(dict)
  author_pov_comments = defaultdict(dict)
  author_revs = defaultdict(dict)
  for ind, r in enumerate(rev_ids):
    with open(os.path.join(path, "revision_%d.json" % r), "r") as f:
      rev = json.load(f)
    authors[r] = rev["user"]
    rev["text"] = format_clean(rev["text"])
    sents = sent_tokenize(rev["text"])
    context_equals, _, deletes, cur_sents = diff(sents, cur_sents, r)
    author_revs[rev["user"]][r] = 1
    if "comment" in rev and "POV" in rev["comment"]:
      if ind > 0:
        print(rev_ids[ind-1])
      for d in deletes:
        pov_sents.append(d[0])
        revid = d[1]
        author = authors[revid]
        author_pov_revs[author][revid] = 1
      for s in context_equals:
        npov_sents.append(s)
      author_pov_comments[rev["user"]][r] = 1
  pov_sents = set(pov_sents)
  npov_sents = set(npov_sents)
  logging.info("%d sentences in POV dispute. ", len(pov_sents))
  with open(os.path.join(path, "pov_sentences.json"), "w") as f:
    for sent in pov_sents:
      f.write(json.dumps(sent) + "\n")
  logging.info("%d sentences not in POV dispute. ", len(npov_sents))
  with open(os.path.join(path, "npov_sentences.json"), "w") as f:
    for sent in npov_sents:
      f.write(json.dumps(sent) + "\n")

  logging.info("Total Number of Authors: %d", len(author_revs.keys()))
  logging.info("Total Number of Revisions: %d", len(rev_ids))
  logging.info("Authors with POV edits: %d", len(author_pov_revs.keys()))
  logging.info("Authors with POV comments: %d", len(author_pov_comments.keys()))
  logging.info("Author Overlap: %d", len(set(author_pov_revs.keys())&
                                         set(author_pov_comments.keys())))
  freq1 = [k for k in author_pov_revs.keys()
           if len(author_revs[k].keys()) >= 20]
  freq2 = [k for k in author_pov_comments.keys()
           if len(author_revs[k].keys()) >= 20]
  logging.info("Frequent Editor Overlap: (%d, %d) -> %d",
               len(freq1), len(freq2), len(set(freq1)&set(freq2)))


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  logging.getLogger().setLevel(logging.INFO)
  # input/output parameters.
  parser.add_argument("--input_path",
                      default=os.environ["HOME"],
                      help="input storage.")
  known_args, pipeline_args = parser.parse_known_args()
  run(known_args)
