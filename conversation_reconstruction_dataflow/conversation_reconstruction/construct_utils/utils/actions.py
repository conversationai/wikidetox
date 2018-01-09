# -*- coding: utf-8 -*-

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
       cont = action['content'][action['content'].find('[OUTDENT: ') + 10 :]
       cont = cont[:cont.find(']')]
       indentation += int(cont) 
    action['user_id'] = rev['user_id']
    action['user_text'] = rev['user_text']
    action['timestamp'] = rev['timestamp']
    action['parent_id'] = None
    if action['indentation'] == -1:
        action['type'] = 'SECTION_CREATION'
    else:
        action['type'] = 'COMMENT_ADDING'
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
    action['type'] = 'COMMENT_REMOVAL'
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
       cont = action['content'][action['content'].find('[OUTDENT: ') + 10 :]
       cont = cont[:cont.find(']')]
       indentation += int(cont) 

    action['user_id'] = rev['user_id']
    action['user_text'] = rev['user_text']
    action['timestamp'] = rev['timestamp']
    action['type'] = 'COMMENT_MODIFICATION'
    
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
    action['type'] = 'COMMENT_REARRANGEMENT'
    
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
    action['type'] = 'COMMENT_RESTORATION'
    
    action['replyTo_id'] = None
    
    return action
