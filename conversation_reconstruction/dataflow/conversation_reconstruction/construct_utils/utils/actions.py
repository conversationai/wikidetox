# -*- coding: utf-8 -*-
"""
Copyright 2017 Google Inc.
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
"""



from __future__ import absolute_import, division, print_function

import re
from collections import defaultdict
from .insert_utils import *

def comment_adding(insert_op, rev, page_actions):
    action = {}
    action['indentation'] = get_indentation(insert_op['tokens'])
    action['rev_id'] = rev['rev_id']
    action['id'] = str(rev['rev_id']) + '.' + str(insert_op['b1']) + '.' + str(insert_op['a1'])
    action['content'] = ''.join(insert_op['tokens'])
    indentation = action['indentation']
    if '[OUTDENT: ' in action['content']:
       indentation += locate_last_indentation(page_actions, insert_op['b1']) + 1

    action['user_id'] = rev['user_id']
    action['user_text'] = rev['user_text']
    action['timestamp'] = rev['timestamp']
    action['parent_id'] = None
    if action['indentation'] == -1:
        action['type'] = 'CREATION'
    else:
        action['type'] = 'ADDITION'
    action['replyTo_id'] = locate_replyTo_id(page_actions, insert_op['b1'], indentation)
    return action, insert_op['b1'], action['id'], action['indentation']

def comment_removal(removal_info, rev):
    removed_action, op = removal_info

    action = {}
    action['indentation'] = removed_action[1] 
    action['id'] = str(rev['rev_id']) + '.' + str(op['b1']) + '.' + str(op['a1'])
    action['rev_id'] = rev['rev_id']
    action['content'] = ''.join(op['tokens'])
    action['user_id'] = rev['user_id']
    action['user_text'] = rev['user_text']
    action['timestamp'] = rev['timestamp']
    action['parent_id'] = None
    action['type'] = 'DELETION'
    action['parent_id'] = removed_action[0]
    action['replyTo_id'] = None
    return action

def comment_modification(prev_id, tokens, new_action_start, new_action_end, rev, page_actions, old_action_start):
    action = {}
    action['indentation'] = get_indentation(tokens)
    indentation = action['indentation']

    action['id'] = str(rev['rev_id']) + '.' + str(new_action_start) + '.' + str(old_action_start) 
    action['rev_id'] = rev['rev_id']
    action['parent_id'] = prev_id
    action['content'] = ''.join(tokens)
    if '[OUTDENT: ' in action['content']:
       indentation += locate_last_indentation(page_actions, new_action_start) + 1

    action['user_id'] = rev['user_id']
    action['user_text'] = rev['user_text']
    action['timestamp'] = rev['timestamp']
    action['type'] = 'MODIFICATION'
    action['replyTo_id'] = locate_replyTo_id(page_actions, new_action_start, indentation)
    return action, new_action_start, action['id'], action['indentation']

def comment_rearrangement(prev_id, tokens, new_action_start, rev, old_action_start):
    action = {}
    action['indentation'] = get_indentation(tokens)

    action['id'] = str(rev['rev_id']) + '.' + str(new_action_start) + '.' + str(old_action_start)
    action['rev_id'] = rev['rev_id']
    action['parent_id'] = prev_id
    action['content'] = ''.join(tokens)
    action['user_id'] = rev['user_id']
    action['user_text'] = rev['user_text']
    action['timestamp'] = rev['timestamp']
    action['type'] = 'REARRANGEMENT'
    
    action['replyTo_id'] = None
    
    return action

def comment_restoration(prev_id, tokens, new_action_start, rev, old_action_start):
    action = {}
    action['indentation'] = get_indentation(tokens)
    action['id'] = str(rev['rev_id']) + '.' + str(new_action_start) + '.' + str(old_action_start)
    action['rev_id'] = rev['rev_id']
    action['parent_id'] = prev_id
    action['content'] = ''.join(tokens)
    action['user_id'] = rev['user_id']
    action['user_text'] = rev['user_text']
    action['timestamp'] = rev['timestamp']
    action['type'] = 'RESTORATION'
    
    action['replyTo_id'] = None
    
    return action
