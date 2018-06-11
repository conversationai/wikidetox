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

Optional:
  -p [--page_ids] PAGE_ID_LIST

This tests the functionality on chosen pages, note that you need to download these pages first using fetch_testdata.py in construct_utils.

  -l [--test_loading_on] REVISION_LIST

The conversation constructor has the functionality of saving the intermediate page state in order to load and continue on it. This should provide a list of revisions that you want to test the loading functionality on.

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import copy
import logging
import unittest
import resource
import argparse
import copy
from construct_utils.conversation_constructor import Conversation_Constructor

default_page_ids = []
# PAGE 34948919, 15854766, 32094486, 43758735, 22811813: testing on memory usage
# PAGE 9373473: REVISION 479969745, test on reconstruction correctness
# PAGE 476334: REVISION 74126950, error reconstruction
# SUGGESTED TESTs: 28031
default_load_test = [493084502, 305838972]

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
          for ind, line in enumerate(f):
               revision = json.loads(line)
               cnt += 1
               last_revision = revision['rev_id']
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
               logging.info("USRLOG: revision %d processed, number %d." % (revision['rev_id'], ind))
               if cnt % LOG_INTERVAL == 0 and cnt and not(page_state == None):
                 # Reload after every LOG_INTERVAL revisions to keep the low memory
                 # usage.
                  processor = Conversation_Constructor()
                  second_last_page_state = copy.deepcopy(page_state)
                  processor.load(page_state['deleted_comments'])
        if p == "dummy_test":
           with open("construct_utils/testdata/%s_ans.json" % p, "r") as f:
              standard_ans = json.load(f)
           self.assertEqual(''.join(ans), standard_ans)

if __name__ == '__main__':
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
  memory_boundary = 1000000 # in KB
  unittest.main()
