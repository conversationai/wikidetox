# -*- coding: utf-8 -*-
"""
copyright 2018 google inc.
licensed under the apache license, version 2.0 (the "license");
you may not use this file except in compliance with the license.
you may obtain a copy of the license at

    http://www.apache.org/licenses/license-2.0

unless required by applicable law or agreed to in writing, software
distributed under the license is distributed on an "as is" basis,
without warranties or conditions of any kind, either express or implied.
see the license for the specific language governing permissions and
limitations under the license.

-------------------------------------------------------------------------------

This is a testing framework to test the functionality of conversation constructor.

Run with default setting:
  python conversation_tester.py

The conversation constructor has the functionality of saving the intermediate page state in order to load and continue on it. This should provide a list of revisions that you want to test the loading functionality on.

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import datetime
import copy
import logging
import unittest
import resource
import argparse
import copy
from construct_utils.conversation_constructor import Conversation_Constructor
from construct_utils.utils.third_party.rev_clean import clean_html

default_page_ids = [2609426] #23031, 23715982, 26647, 10555, 21533114, 23715934, 476334, 14496]
# Suggestion on test pages:
# PAGE 32094486: Formatted in tables, mostly in Spanish, suggested to test
# diff algorithm, encodings.
# PAGE 34948919, 15854766, 43758735, 22811813, 28031: Long pages with long deletions,
# suggested to test on memory usage.
# PAGE 9373474: REVISION 479969745, test on reconstruction correctness.
# PAGE 476334: REVISION 74126950, error reconstruction.
# PAGE 32094486: diff testing on REVISION 438455007.
# DEFAULT TEST: dummy_test, test on reconstruction correctness.
default_load_test = [493084502, 305838972]

TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

def merge(ps1, ps2):
     # Merge two page states, ps1 is the later one
     deleted_ids_ps2 = {d[1]:d for d in ps2['deleted_comments']}
     deleted_ids_ps1 = {d[1]:d for d in ps1['deleted_comments']}
     deleted_ids_ps2.update(deleted_ids_ps1)
     extra_ids = [key for key in deleted_ids_ps2.keys() if not(key in deleted_ids_ps1)]
     ret_p = copy.deepcopy(ps1)
     ret_p['deleted_comments'] = list(deleted_ids_ps2.values())
     conv_ids = ps2['conversation_id']
     auth = ps2['authors']
     ret_p['conversation_id'] = ret_p['conversation_id']
     ret_p['authors'] = ret_p['authors']
     for i in extra_ids:
         ret_p['conversation_id'][i] = conv_ids[i] 
         ret_p['authors'][i] = auth[i]
     ret_p['conversation_id'] = ret_p['conversation_id']
     ret_p['authors'] = ret_p['authors']
     return ret_p


class TestReconstruction(unittest.TestCase):
  def test_reconstruction(self):
     for p in PAGES:
        with open("page_states.json", "r") as w:
          (page_state, latest_content, last_rev_id) = json.load(w)

        logging.info("TEST LOG: testing starts on page %s" % str(p))
        processor = Conversation_Constructor()
        cnt = 0
        last_revision = "None"
        page_state = None
        second_last_page_state = None
        last_revision_to_save = None
        last_loading = 0
        latest_content = ""
        ans = []
        if not(p == "dummy_test"):
           filename = "construct_utils/testdata/reversed_page_%d.json" % p
        else:
           filename = "construct_utils/testdata/%s.json" % p
        with open(filename, "r") as f:
          last_week = -1
          for ind, line in enumerate(f):
               revision = json.loads(line)
               last_revision = revision['rev_id']
               week = datetime.datetime.strptime(revision['timestamp'], TIMESTAMP_FORMAT).isocalendar()[1]
               year = datetime.datetime.strptime(revision['timestamp'], TIMESTAMP_FORMAT).year
               if revision['rev_id'] < last_rev_id:
                 print(week, year)
                 continue
               cnt += 1
               if ((cnt % LOG_INTERVAL == 0 and cnt) \
                   or (last_week >= 0 and last_week != week))\
                  and not(page_state == None):
                 # Reload after every LOG_INTERVAL revisions to keep the low memory
                 # usage.
                  memory_usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                  logging.info("MENMORY BEFORE RELOADING : %d KB" % memory_usage)
                  processor = Conversation_Constructor()
                  #second_last_page_state = copy.deepcopy(page_state)
                  processor.load(page_state['deleted_comments'])
                  del page_state['deleted_comments']
                  page_state['deleted_comments'] = []
                  print(year, week)
                  memory_usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                  logging.info("MENMORY AFTER RELOADING : %d KB" % memory_usage)

               if revision['rev_id'] in LOADING_TEST: 
                  if second_last_page_state:
                     page_state_test = merge(page_state, second_last_page_state)
                  else:
                     page_state_test = copy.deepcopy(page_state)
                  processor_test = Conversation_Constructor()
                  processor_test.load(page_state_test['deleted_comments'])
                  _, actions_test, _ = \
                     processor.process(page_state_test, latest_content, revision)
               page_state, actions, latest_content = \
                   processor.process(page_state, latest_content, revision)
               memory_usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
               self.assertLessEqual(memory_usage, memory_boundary)
               if revision['rev_id'] in LOADING_TEST:
                  self.assertEqual(json.dumps(actions), json.dumps(actions_test))
               ids = []
               for action in actions:
                  ids.append(action['id'])
                  ans.append("ID %s, TYPE %s, CONTENT: %s" % (action['id'], action['type'], action['content']))
                  logging.debug("ID %s, TYPE %s, CONTENT: %s" % (action['id'], action['type'], action['content']))
               assert(len(set(ids)) == len(actions))
               if revision['rev_id'] == 479969745:
                  self.assertEqual(len(actions), 2)
               logging.info("USRLOG: revision %d processed, number %d on page %s." % (revision['rev_id'], ind, p))
               last_week = week
        if p == "dummy_test":
           with open("construct_utils/testdata/%s_ans.json" % p, "r") as f:
              standard_ans = json.load(f)
           self.assertEqual(''.join(ans), standard_ans)

if __name__ == '__main__':
  logging.basicConfig(filename="test_debug.log", level=logging.DEBUG)
  logging.getLogger().setLevel(logging.DEBUG)
  parser = argparse.ArgumentParser()
  parser.add_argument('-p', '--page_ids', dest='page_ids',\
                      nargs='+', default=default_page_ids, type=int)
  parser.add_argument('-l', '--test_loading_on', dest='load_test',\
                      nargs='+', default=default_load_test, type=int)
  PAGES = parser.parse_args().page_ids
  PAGES.append("dummy_test")
  LOADING_TEST = parser.parse_args().load_test
  LOG_INTERVAL = 100
  memory_boundary = 2000000 # in KB
  unittest.main()
