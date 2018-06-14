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
import copy
from collections import defaultdict

def get_section_tokens(tokens, line):
    sofar = ""
    for tok in tokens:
        if line in sofar:
            break
        else:
            yield tok
            sofar += tok

def isheading(line):
    front_cnt = re.serach("^=+", x).group(0)
    back_cnt = re.search("^=+", x[::-1]).group(0)
    if front_cnt == back_cnt and front_cnt > 0:
       return True

def divide_into_section_headings_and_contents(op, content):
    content += '==LASTLINESYMBOL==\n'
    lines = content.splitlines()
    comments = []
    last_pos = 0
    last_tok = 0
    for line in lines:
        if isheading(line):
            cur_pos = content.find(line)
            cur_tok = last_tok + len(content[:cur_pos])
            comments.append([content[:cur_pos], last_tok, cur_tok])
            last_tok = cur_tok
            cur_tok = cur_tok + len(line) + 1
            comments.append([line, last_tok, cur_tok])
            content = content[cur_pos + len(line) + 1:]
            last_tok = cur_tok
    for tokens, b1, b2 in comments[:-1]:
        if b2 > b1:
            comment_op = copy.deepcopy(op)
            comment_op['tokens'] = op['tokens'][b1:b2]
            comment_op['b1'] = op['b1'] + b1
            comment_op['b2'] = op['b1'] + b2
            yield comment_op

def find_pos(pos, lst):
    h = 0
    t = len(lst) - 1
    mid = int((h + t) / 2)
    ans = -1
    while not(h > t):
        if pos >= lst[mid]:
            ans = mid
            h = mid + 1
        else:
            t = mid - 1
        mid = int((h + t) / 2)
    return ans

def get_action_start(action_lst, token_position):
    ans = find_pos(token_position, action_lst)
    if (action_lst[ans] == token_position and not(token_position == 0)):
        return action_lst[ans-1]
    else:
        return action_lst[ans]

def get_action_end(action_lst, token_position):
    ans = find_pos(token_position, action_lst)
    return action_lst[ans + 1]

def is_in_boundary(x, start, end):
    return (x >= start and x <= end)

def locate_replyTo_id(actions, action_pos, action_indentation):
    action_lst = sorted(list(actions.keys()))
    ind = find_pos(action_pos, action_lst)
    ret = None
    while ind >= 0:
        if actions[action_lst[ind]][1] < action_indentation:
            return actions[action_lst[ind]][0]
        ind -=1
    return ret

def locate_last_indentation(actions, action_pos):
    action_lst = sorted(list(actions.keys()))
    ind = find_pos(action_pos, action_lst)
    ret = None
    while ind >= 0:
        return actions[action_lst[ind]][1]
    return 0

def get_firstline(tokens):
    lines = "".join(tokens).splitlines()
    firstline = ""
    for l in lines:
        if not(l == ""):
            firstline = l
            break
    return firstline

def get_indentation(tokens):
    cnt = 0
    # If this is a creation of a section.
    firstline = get_firstline(tokens)
    if isheading(firstline):
        return -1
    # If this is a normal section.
    for t in firstline:
        if t == ':' or t == '*':
            cnt += 1
        else:
            break
    return cnt

def locate_new_token_pos(old_pos, ops, errorchoice='raise_error'):
    new_pos = 0
    ops = sorted(ops, key=lambda k: (not(k['name'] == 'equal'), k['a1']))
    for op in ops:
        if op['name'] == 'equal':
          if is_in_boundary(old_pos, op['a1'], op['a2']):
             if errorchoice == 'left_bound':
                new_pos = op['b1'] + old_pos - op['a1']
             elif not(new_pos):
                new_pos = op['b1'] + old_pos - op['a1']
        else:
            if op['name'] == 'delete':
                if old_pos >= op['a1'] and old_pos < op['a2']:
                    if errorchoice == 'raise_error':
                        raise ValueError('locate_new_token_pos : Token has been deleted')
                    else:
                        if errorchoice == 'right_bound':
                            new_pos = op['b2']
                        else:
                            new_pos = op['b1']
            if old_pos == op['a2']:
              if errorchoice == 'left_bound' and op['name'] == 'insert':
                   new_pos = op['b1']
              if errorchoice != 'left_bound':
                   new_pos = op['b2']
    return new_pos
