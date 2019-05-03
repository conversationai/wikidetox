"""Copyright 2017 Google Inc. Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.

You may obtain a copy of the License at
    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

-------------------------------------------------------------------------------
"""

# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function
from __future__ import unicode_literals
from builtins import *
from future.builtins.disabled import *

import copy
import json
from collections import defaultdict
from noaho import NoAho
import re
import sys
import traceback
import atexit
import os
import logging
import resource
from .utils.third_party import diff_match_patch as dmp_module
from .utils.third_party.rev_clean import clean, clean_html
from .utils.insert_utils import *
from .utils.actions import *


def insert(rev, page, previous_comments, COMMENT_LOWERBOUND):
  """
       Given the current revision, page state and previously deleted comments.
       This function compares the latest processed revision with the input
       revision
       and determine what kind of conversation actions were done to the page.
       It returns the list of actions and the updated page state.

       One main component here is the page state -- page['actions'],
       it's a dictionary with the key as an offset on the page representing a
       starting position
       of an action, and the value is a tuple (action_id, indentation).
       The endding offset is also included in the list, with (-1, -1) denoting
       the boundary of
       the page.
    """
  comment_removals = []
  tmp_rmvs = []
  comment_additions = []
  removed_actions = {}
  old_actions = sorted(page['actions'].keys())
  modification_actions = defaultdict(int)
  rev_text = rev['text']
  # Process each operation in the diff
  modification_diffs = []
  for op in rev['diff']:
    # Ignore parts that remain the same
    if op['name'] == 'equal':
      modification_diffs.append(op)
      continue
    if op['name'] == 'insert':
      content = ''.join(op['tokens'])
      if content == '':
        continue
      logging.debug('INSERT %s OFFSET (%d, %d)', content, op['b1'], op['b2'])
      if (op['tokens'][0] == '\n' or op['b1'] == 0 or\
         (op['b1'] > 0 and rev_text[op['b1'] - 1] == '\n')) and\
         (op['b2'] == len(rev_text) or op['tokens'][-1] == '\n'):
        # Identify replies inline.
        if not (op['a1'] in old_actions):
          old_actions.append(op['a1'])
          the_action = get_action_start(old_actions, op['a1'])
          page['actions'][op['a1']] = page['actions'][the_action]
        # If the current insertion is adding a new comment
        for c in divide_into_section_headings_and_contents(op, content):
          # Divide the newly added content into headings and contents
          comment_additions.append(c)
      else:
        modification_diffs.append(op)
  logging.debug('OLD ACTIONS: %s', json.dumps(old_actions))
  logging.debug('OLD ACTION LENGTH: %d', len(old_actions))
  old_actions = sorted(old_actions)
  for op in rev['diff']:
    if op['name'] == 'delete':
      content = ''.join(op['tokens'])
      # Deletions may remove multiple comments at the same time
      # Here is to locate the boundary of the deletion in the old revision
      delete_start = op['a1']
      delete_end = op['a2']
      deleted_action_start = find_pos(delete_start, old_actions)
      deleted_action_end = find_pos(delete_end, old_actions)
      deleted_action_end = deleted_action_end + 1
      logging.debug('DELETE %d %d', op['a1'], op['a2'])
      logging.debug('DELETED ACTION : (%d, %d)', deleted_action_start,
                    deleted_action_end)
      start_token = 0
      # If the deletion removes/modifies multiple coments,
      # divide the deletion into parts.
      for ind, act in enumerate(
          old_actions[deleted_action_start:deleted_action_end]):
        if act == delete_end:
          break
        partial_op = {}
        partial_op['a1'] = max(delete_start, act)
        partial_op['a2'] = min(delete_end,
                               old_actions[deleted_action_start + ind + 1])
        partial_op['b1'] = op['b1']
        partial_op['b2'] = op['b2']
        partial_op['tokens'] = op['tokens'][start_token:partial_op['a2'] -
                                            partial_op['a1'] + start_token]
        start_token += partial_op['a2'] - partial_op['a1']
        # Determine if the subset of the deletion is a comment removal
        # or modification.
        if delete_start > act or act == old_actions[deleted_action_end - 1]:
          logging.debug('MODIFICATION ON %d', act)
          modification_actions[act] = True
          modification_diffs.append(op)
        else:
          comment_removals.append([page['actions'][act], partial_op])
          removed_actions[act] = True
  for op in modification_diffs:
    if op['name'] == 'insert':
      content = ''.join(op['tokens'])
      logging.debug('MODIFICATION INSERT CONTENT : %s, OFFSET (%d, %d)',
                    content, op['b1'], op['b2'])
      # If the current insertion is modifying an existed comment
      old_action_start = get_action_start(old_actions, op['a1'])
      for ind, x in enumerate(old_actions):
        if x == op['a1']:
          break
      while (old_action_start in removed_actions and ind < len(old_actions)):
        old_action_start = old_actions[ind]
        ind += 1
      if ind >= len(old_actions):
        for c in divide_into_section_headings_and_contents(op, content):
          # Divide the newly added content into headings and contents
          comment_additions.append(c)
        del op
      else:
        # Find the corresponding existed comment and set a flag
        modification_actions[old_action_start] = True
  modification_diffs = sorted(modification_diffs, key=lambda k: k['a1'])
  rearrangement = {}
  updated_removals = []
  end_tokens = []
  updated_actions = []
  # The comment rearrangements are comments longer then a thereshold longer
  # then a thereshold that is removed and added back in the same revision.
  # We compare the detected removals with additions to identify them.
  for removal in comment_removals:
    if len(removal[1]['tokens']) <= COMMENT_LOWERBOUND:
      updated_removals.append(removal)
      continue
    removed = ''.join(removal[1]['tokens'])
    logging.debug('REMOVED: %s', removed)
    rearranged = False
    updated_additions = []
    for ind, insert in enumerate(comment_additions):
      inserted = ''.join(insert['tokens'])
      # Determine if the removed content is part of an addition
      if removed in inserted:
        # Update the rearranagement action
        start_pos = inserted.find(removed)
        start_tok = len(inserted[:start_pos])
        end_tok = start_tok + len(removal[1]['tokens'])
        end_tokens.append((start_tok + insert['b1'], end_tok + insert['b1']))
        rearrangement[removal[1]['a1']] = start_tok + insert['b1']
        logging.debug('REARRANGEMENT FOUND: Offset (%d, %d).', removal[1]['a1'],
                      start_tok + insert['b1'])
        tmp_ins = []
        # Divide the comment addition
        if not (start_tok == 0):
          tmp_in = copy.deepcopy(insert)
          tmp_in['b2'] = start_tok + insert['b1']
          tmp_in['tokens'] = insert['tokens'][:start_tok]
          tmp_ins.append(tmp_in)
        if not (end_tok == len(insert['tokens'])):
          tmp_in = copy.deepcopy(insert)
          tmp_in['b1'] = end_tok + insert['b1']
          tmp_in['tokens'] = insert['tokens'][end_tok:]
          tmp_ins.append(tmp_in)
        # Update the comment additions
        for tmp_in in tmp_ins:
          updated_additions.append(tmp_in)
        for tmp_in in comment_additions[ind + 1:]:
          updated_additions.append(tmp_in)
        rearranged = True
        break
      updated_additions.append(insert)
    if not (rearranged):
      updated_removals.append(removal)
    else:
      comment_additions = updated_additions
  comment_removals = updated_removals

  # Record removal actions.
  for removal in comment_removals:
    updated_actions.append(comment_removal(removal, rev))
  # Update offsets of existed actions in the current revision.
  updated_page = {}
  updated_page['page_id'] = rev['page_id']
  updated_page['actions'] = {}
  updated_page['page_title'] = rev['page_title']
  for act in old_actions:
    if not (act in modification_actions or act in removed_actions):
      # If an action is modified, it will be located later.
      # If an action is removed, it will be ignored in the updated page state.
      new_pos = locate_new_token_pos(act, rev['diff'])
      # Otherwise update action offsets for old actions.
      if page['actions'][act] == (-1, -1):
        logging.debug('DOCUMENT END: %d -> %d.', act, new_pos)
      updated_page['actions'][new_pos] = page['actions'][act]
    # If an action is in rearrangement(it will also be in the removed action
    # set). The updated action should be registered into its newly rearranged
    # location.
    if act in rearrangement:
      updated_page['actions'][rearrangement[act]] = page['actions'][act]
  # Locate the updated offset of existed actions that were modified in the current revision
  for old_action_start in modification_actions.keys():
    # Locate the old and new starting and ending offset position of the action
    old_action = page['actions'][old_action_start][0]
    old_action_end = get_action_end(old_actions, old_action_start)
    new_action_start = locate_new_token_pos(old_action_start,
                                            modification_diffs, 'left_bound')
    new_action_end = locate_new_token_pos(old_action_end, modification_diffs,
                                          'right_bound')
    logging.debug('OLD %d -> %d', old_action_end, new_action_end)
    logging.debug('OLD %d -> %d', old_action_start, new_action_start)
    # Get the updated text
    tokens = rev['text'][new_action_start:new_action_end]
    # Create the action modification object and register the new action
    new_action, new_pos, new_id, new_ind = comment_modification(
        old_action, tokens, new_action_start, new_action_end, rev,
        updated_page['actions'], old_action_start)
    updated_actions.append(new_action)
    # Update the actionson the page state
    updated_page['actions'][new_pos] = (new_action['id'], new_ind)
  updated_additions = []
  # Comment restorations are previouly deleted comments being added back.
  # Identifying comment restoration.
  for insert_op in comment_additions:
    tokens = insert_op['tokens']
    text = ''.join(tokens)
    last_pos = 0
    # Using a trie package to locate substrings of previously deleted
    # comments present in the current addition action.
    for k1, k2, val in previous_comments.findall_long(text):
      # If a valid match was found, the addition content will be
      # decomposed.
      last_op = {}
      last_op['tokens'] = tokens[last_pos:k1]
      # For parts that are not a restoration, it will be added back to the
      # addition list.
      if not (last_op['tokens'] == ''):
        last_op['a1'] = insert_op['a1']
        last_op['a2'] = insert_op['a2']
        last_op['b1'] = last_pos + insert_op['b1']
        last_op['b2'] = k1 + insert_op['b1']
        updated_additions.append(last_op)
      # Create the restoration object and update its offset on page state.
      updated_actions.append(
          comment_restoration(val[0], tokens[k1:k2], k1 + insert_op['b1'], rev,
                              insert_op['a1']))
      updated_page['actions'][k1 + insert_op['b1']] = val
      end_tokens.append((k1 + insert_op['b1'], k2 + insert_op['b1']))
      last_pos = k2
    last_op = {}
    last_op['a1'] = insert_op['a1']
    last_op['a2'] = insert_op['a2']
    last_op['b1'] = last_pos + insert_op['b1']
    last_op['b2'] = insert_op['b2']
    if last_op['b2'] - last_op['b1'] > 0:
      last_op['tokens'] = insert_op['tokens'][last_pos:]
      updated_additions.append(last_op)
  comment_additions = updated_additions
  # Create the addition object and update the offsets on page state.
  for insert_op in comment_additions:
    new_action, new_pos, new_id, new_ind = comment_adding(
        insert_op, rev, updated_page['actions'])
    updated_page['actions'][new_pos] = (new_id, new_ind)
    updated_actions.append(new_action)
    end_tokens.append((insert_op['b1'], insert_op['b2']))
  # Record all actions onto page state.
  for start_tok, end_tok in end_tokens:
    if not (end_tok in updated_page['actions']):
      tmp_lst = sorted(list(updated_page['actions'].keys()))
      last_rev = tmp_lst[find_pos(start_tok, tmp_lst) - 1]
      logging.debug('ACTION OFFSETS: (%d, %d)', start_tok, end_tok)
      updated_page['actions'][end_tok] = updated_page['actions'][last_rev]
  logging.debug('ACTIONS FOUND : %s.',
                ','.join([action['type'] for action in updated_actions]))
  # Sanity checks:
  # The page states must start with 0 and end with the last token.
  assert (0 in updated_page['actions'])
  eof = max(list(updated_page['actions'].keys()))
  # (-1, -1) only denotes the page boundary.
  for action, val in updated_page['actions'].items():
    if not (action == eof):
      assert not (val == (-1, -1))
  assert eof == len(rev['text'])
  # The page state value of the page boundary must be (-1, -1).
  assert updated_page['actions'][eof] == (-1, -1)
  updated_actions = sorted(
      updated_actions, key=lambda k: int(k['id'].split('.')[1]))
  return updated_actions, updated_page


class Conversation_Constructor:

  def __init__(self):
    self.COMMENT_LOWERBOUND = 10
    self.COMMENT_UPPERBOUND = 1000
    # Deleted comments with less than this number of tokens will not be recorded
    # thus not considered in comment restoration actions to reduce confusion.
    self.deleted_records = {}

  def page_creation(self, rev):
    page = {}
    page['page_id'] = rev['page_id']
    page['actions'] = {}
    page['page_title'] = rev['page_title']
    page['actions'][0] = (-1, -1)
    return page

  def load(self, deleted_comments):
    """
          Load the previous page state, deleted comments and other information
        """
    self.deleted_records = {}
    self.previous_comments = NoAho()
    for pair in deleted_comments:
      self.previous_comments.add(pair[0], (pair[1], int(pair[2])))
      self.deleted_records[pair[1]] = True
    return

  def convert_diff_format(self, x, a, b):
    ret = x
    if x['name'] == 'insert':
      ret['tokens'] = b[x['b1']:x['b2']]
    if x['name'] == 'delete':
      ret['tokens'] = a[x['a1']:x['a2']]
    return ret

  def mydiff_toDelta(self, diffs):
    """Crush the diff into a list of dictionary indicating changes

         from one document to another. Operations are dictionary record
         with name (insert, delete, equal) and offsets (in original text
         and resulted text).

         Args:
           diffs: Array of diff tuples.

         Returns:
           Deltas.
         """
    text = []
    a = 0
    b = 0
    DIFF_DELETE = -1
    DIFF_INSERT = 1
    DIFF_EQUAL = 0

    for (op, data) in diffs:
      if op == DIFF_INSERT:
        yield ({
            'name': 'insert',
            'a1': a,
            'a2': a,
            'b1': b,
            'b2': b + len(data)
        })
        b += len(data)
      elif op == DIFF_DELETE:
        yield ({
            'name': 'delete',
            'a1': a,
            'a2': a + len(data),
            'b1': b,
            'b2': b
        })
        a += len(data)
      elif op == DIFF_EQUAL:
        yield ({
            'name': 'equal',
            'a1': a,
            'a2': a + len(data),
            'b1': b,
            'b2': b + len(data)
        })
        a += len(data)
        b += len(data)

  def clean_dict(self, page, the_dict):
    """
          We only store the information of currently 'alive' actions.
          Definition of alive:
             - The action was a deletion happened recently, hence might be
             restored later.
             - The action is still present on the page, hence might be
             modified/removed/replied to.
        """
    keylist = the_dict.keys()
    ret = the_dict
    alive_actions = set([action[0] for action in page['actions'].values()])
    for action in keylist:
      if not (action in alive_actions or action in self.deleted_records):
        del ret[action]
    return ret

  def process(self, page_state, latest_content, rev):
    logging.debug('DEBUGGING MODE on REVISION %s', rev['rev_id'])
    memory_usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    logging.debug('MOMERY USAGE BEFORE ANYTHING: %d KB.', memory_usage)
    # Clean the HTML format of the revision.
    rev['text'] = clean_html(rev['text'])
    # Compute the diff between the latest processed revision and the current
    # one.
    dmp = dmp_module.diff_match_patch()
    logging.debug('LENGTH : %d -> %d', len(latest_content), len(rev['text']))
    diff = dmp.diff_main(latest_content, rev['text'], False)
    dmp.diff_cleanupSemantic(diff)
    delta = self.mydiff_toDelta(diff)
    rev['diff'] = sorted([self.convert_diff_format(x, latest_content, rev['text']) \
                          for x in delta], key=lambda k: k['a1'])
    # Create a new page if this page was never processed before.
    if not (page_state):
      self.previous_comments = NoAho()
      old_page = self.page_creation(rev)
      page_state = {'rev_id': int(rev['rev_id']), \
                    'timestamp': rev['timestamp'], \
                    'page_id': rev['page_id'], \
                    'deleted_comments': [], \
                    'conversation_id': {}, \
                    'authors': {},
                    'ancestor_id': {}}
    else:
      page_state['rev_id'] = int(rev['rev_id'])
      page_state['timestamp'] = rev['timestamp']
      old_page = page_state['page_state']
    memory_usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    logging.debug('MOMERY USAGE BEFORE PROCESSING: %d KB.', memory_usage)
    # Process the revision to get the actions and update page state
    actions, updated_page = insert(rev, old_page, self.previous_comments,
                                   self.COMMENT_LOWERBOUND)
    page_state['page_state'] = updated_page
    # Post process of the actions:
    for action in actions:
      # If the action is adding new content
      # - locate which conversation does it belong to
      # - record the name of the author into the author list of the comment
      if action['type'] == 'ADDITION' or action['type'] == 'MODIFICATION' \
         or action['type'] == 'CREATION':
        if action['replyTo_id'] == None:
          page_state['conversation_id'][action['id']] = action['id']
        else:
          page_state['conversation_id'][action['id']] = \
              page_state['conversation_id'][action['replyTo_id']]
        if action['type'] == 'MODIFICATION':
          page_state['authors'][action['id']] = \
              set(page_state['authors'][action['parent_id']])
          page_state['authors'][action['id']].add(
              (action['user_id'], action['user_text']))
          page_state['ancestor_id'][action['id']] = \
              page_state['ancestor_id'][action['parent_id']]
        else:
          page_state['authors'][action['id']] = \
              set([(action['user_id'], action['user_text'])])
          page_state['ancestor_id'][action['id']] = action['id']
      else:
        page_state['authors'][action['id']] = \
            set(page_state['authors'][action['parent_id']])
        page_state['ancestor_id'][action['id']] = \
            page_state['ancestor_id'][action['parent_id']]

      # Removed and restored comments are considered
      # belonging to the same conversation as its original version.
      if action['type'] == 'DELETION':
        page_state['conversation_id'][action['id']] = \
                 page_state['conversation_id'][action['parent_id']]
      if action['type'] == 'RESTORATION':
        page_state['conversation_id'][action['id']] = \
                 page_state['conversation_id'][action['parent_id']]
      action['conversation_id'] = page_state['conversation_id'][action['id']]
      action['authors'] = list(page_state['authors'][action['id']])
      action['page_id'] = rev['page_id']
      action['page_title'] = rev['page_title']
      action['cleaned_content'] = clean(action['content'])
      action['ancestor_id'] = page_state['ancestor_id'][action['id']]
      # If a comment is deleted, it will be added to a list used for
      # identifying restoration actions later. Note that comments that
      # deleted two weeks ago will be removed from the list to ensure
      # memory efficiency. Also comments that are too long or too short
      # are ignored in this case.
      if action['type'] == 'DELETION' and\
          len(action['content']) > self.COMMENT_LOWERBOUND and\
          len(action['content']) < self.COMMENT_UPPERBOUND:
        page_state['deleted_comments'].append(
            (''.join(action['content']), action['parent_id'],
             action['indentation']))
        self.deleted_records[action['parent_id']] = True
        self.previous_comments.add(''.join(action['content']),
                                   (action['parent_id'], action['indentation']))

    page_state['conversation_id'] = self.clean_dict(
        updated_page, page_state['conversation_id'])
    page_state['authors'] = self.clean_dict(updated_page, page_state['authors'])
    # Set is not JSON serializable.
    page_state['authors'] = {
        action_id: list(authors)
        for action_id, authors in page_state['authors'].items()
    }
    memory_usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    logging.debug('MOMERY USAGE AFTER POSTPROCESSING: %d KB.', memory_usage)
    return page_state, actions, rev['text']
