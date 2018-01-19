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



from future.builtins.disabled import *
from collections import defaultdict
import copy
import re

def diff_tuning(diffs, text_a, text_b):
    ret = []    
    equals = [op for op in diffs if op['name'] == 'equal']  
    inserts = {}
    for op in diffs:
        if op['name'] == 'insert':
           inserts[op['a1']] = op
    deletes = {}
    for op in diffs:
        if op['name'] == 'delete':
           deletes[op['b1']] = op
    if not(len(equals)):
       return diffs
    previous = equals[0]
    for op in equals[1:]:
        if op['a1'] == previous['a2'] and previous['a2'] in inserts: 
           if text_b[inserts[previous['a2']]['b1']] == text_b[op['b1']] and text_b[op['b1']].type == 'break':
              inserts[previous['a2']]['a1'] += 1
              inserts[previous['a2']]['a2'] += 1
              inserts[previous['a2']]['b1'] += 1
              inserts[previous['a2']]['b2'] += 1
              inserts[previous['a2']]['tokens'] = inserts[previous['a2']]['tokens'][1:] + [inserts[previous['a2']]['tokens'][0]]
              previous['a2'] += 1
              previous['b2'] += 1
              op['a1'] += 1
              op['b1'] += 1
        if op['b1'] == previous['b2'] and previous['b2'] in deletes: 
           if text_a[deletes[previous['b2']]['a1']] == text_a[op['a1']] and text_a[op['a1']].type == 'break':
              deletes[previous['b2']]['a1'] += 1
              deletes[previous['b2']]['a2'] += 1
              deletes[previous['b2']]['b1'] += 1
              deletes[previous['b2']]['b2'] += 1
              deletes[previous['b2']]['tokens'] = deletes[previous['b2']]['tokens'][1:] + [deletes[previous['b2']]['tokens'][0]]
              previous['a2'] += 1
              previous['b2'] += 1
              op['a1'] += 1
              op['b1'] += 1
 
        ret.append(previous)
        previous = op
    ret.append(previous)
    for op in inserts.values(): 
        ret.append(op)
    for op in deletes.values():
        ret.append(op)
    return ret

"""

MATCHING_THERESHOLD = 0.5

def combined(ops):
    ops = sorted(ops, key = lambda op: (op['name'], op['a1'], op['b1']))
    updated_op = []
    
    if ops == []:
        new_op = {}
        new_op['name'] = 'equal'
        new_op['a1'] = 0
        new_op['a2'] = 0
        new_op['b1'] = 0
        new_op['b2'] = 0
        ops = [new_op]
    previous_op = copy.deepcopy(ops[0])
    for op in ops[1:]:
        if op['name'] == previous_op['name'] and op['a1'] == previous_op['a2'] and op['b1'] == previous_op['b2']:
            previous_op['a2'] = op['a2']
            previous_op['b2'] = op['b2']
            if 'tokens' in previous_op:
                for tok in op['tokens']:
                    previous_op['tokens'].append(tok)
        else:
            yield previous_op
            previous_op = copy.deepcopy(op)
    yield previous_op

MIN_NUMBER_WORDS = 0

def divide_into_sequences(cont):
    cur = ""
    token_cnt = 0
    cnt = 0
    for tok in cont:
        if tok.type in ["period", "qmark", "epoint", "comma", "scolon"]: 
           cur += tok
           if token_cnt > MIN_NUMBER_WORDS:
              yield cur.strip()
           token_cnt = 0
           cur = ""
        else:
           if tok.type in ["word", "number"]:
              token_cnt += 1
           cur += tok
    if token_cnt > MIN_NUMBER_WORDS:
       yield cur.strip()

def sequences(cont):
    cur = []
    for tok in cont:
        if tok.type in ["period", "qmark", "epoint", "comma", "scolon"]: 
           cur.append(tok)
           if not(cur == []):
              yield cur
           cur = []
        else:
           cur.append(tok)
    if not(cur == []):
       yield cur

 
MATCHING_SEQUENCE_THERESHOLD = 0.3

def quick_check(a, b):
    a_sequences = divide_into_sequences(a)
    b_sequences = divide_into_sequences(b)
    a_dict = {}
    a_len = 0
    for seq in a_sequences:
        a_dict[seq] = True
        a_len += 1
    matched_potion = 0
    for seq in b_sequences:
        if seq in a_dict:
           matched_potion += 1
    if (matched_potion >= a_len / 2) or (matched_potion >= 1 and a_len <= 10) or (a_len <= 3):
       return True
    return False

def match_seq(a, b):
    lengths = [[0 for j in range(len(b)+1)] for i in range(len(a)+1)]
    tokens = [[0 for j in range(len(b)+1)] for i in range(len(a)+1)]
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            if x == y:
                lengths[i+1][j+1] = lengths[i][j] + 1
                tokens[i+1][j+1] = tokens[i][j] + (1 if x.type == 'word' or x.type == 'number' else 0)
            else:
                lengths[i+1][j+1] = max(lengths[i+1][j], lengths[i][j+1])
                if lengths[i+1][j] > lengths[i][j+1]:
                    tokens[i+1][j+1] = tokens[i+1][j]
                else: 
                    tokens[i+1][j+1] = tokens[i][j+1]
    x, y = len(a), len(b)
    if tokens[x][y] < MATCHING_THERESHOLD * sum([1 if xx.type == 'word' or xx.type == 'number' else 0 for xx in a]):
        return None
    # read the substring out from the matrix
    ops = []
    while x != 0 and y != 0:
        if lengths[x][y] == lengths[x-1][y]:
            new_op = {}
            new_op['name'] = 'delete'
            new_op['a2'] = x
            new_op['a1'] = x - 1
            new_op['b1'] = y
            new_op['b2'] = y
            new_op['tokens'] = [a[x - 1]]
            ops.append(new_op)
            x -= 1
        elif lengths[x][y] == lengths[x][y-1]:
            new_op = {}
            new_op['name'] = 'insert'
            new_op['b2'] = y
            new_op['b1'] = y - 1
            new_op['a1'] = x
            new_op['a2'] = x
            new_op['tokens'] = [b[y - 1]]
            y -= 1
            ops.append(new_op)
        else:
            assert a[x-1] == b[y-1]
            new_op = {}
            new_op['name'] = 'equal'
            new_op['b2'] = y
            new_op['b1'] = y - 1
            new_op['a1'] = x - 1
            new_op['a2'] = x
            ops.append(new_op)
            x -= 1
            y -= 1
    xx = x
    yy = y
    for ax in a[:x][::-1]:
        new_op = {}
        new_op['name'] = 'delete'
        new_op['a2'] = xx 
        xx -= 1
        new_op['a1'] = xx 
        new_op['b1'] = y 
        new_op['b2'] = y 
        new_op['tokens'] = [ax]
        ops.append(new_op)
    for bx in b[:y][::-1]:
        new_op = {}
        new_op['name'] = 'insert'
        new_op['b2'] = yy 
        yy -= 1
        new_op['b1'] = yy 
        new_op['a1'] = x
        new_op['a2'] = x
        new_op['tokens'] = [bx]
        ops.append(new_op)

    return ops

def match(a, b):
    if not(quick_check(a, b)): return None
    a_lines = list(sequences(a)) 
    b_lines = list(sequences(b)) 
    
    lengths = [[0 for j in range(len(b_lines)+1)] for i in range(len(a_lines)+1)]
    matching_res = defaultdict(dict)
    
    matched_x = {}
    matched_y = {}
    cnt = defaultdict(int)
    for i, x in enumerate(a_lines):
        cnt[''.join(x)] += 1

    
    for i, x in enumerate(a_lines):
        matched_x[i] = False
        if cnt[''.join(x)] > 1: 
           continue
        for j, y in enumerate(b_lines):
            if ''.join(x) == ''.join(y) and j not in matched_y:
                matching_res[i][j] = matched(x, y)
                matched_x[i] = True
                matched_y[j] = True
                break
                
    for i, x in enumerate(a_lines):
        for j, y in enumerate(b_lines):
            if (j not in matched_y) and not(matched_x[i]):
                matching_res[i][j] = match_seq(x, y)
            if j in matching_res[i] and not(matching_res[i][j] == None):
                lengths[i+1][j+1] = lengths[i][j] + 1
            else:
                lengths[i+1][j+1] = max(lengths[i+1][j], lengths[i][j+1])
    # read the substring out from the matrix
    ops = []
    x, y = len(a_lines), len(b_lines)
    a_tok = sum([len(a) for a in a_lines])
    b_tok = sum([len(b) for b in b_lines])

    while x != 0 and y != 0:

        if lengths[x][y] == lengths[x-1][y]:
            a = a_lines[x-1]
            new_op = {}
            new_op['name'] = 'delete'
            new_op['a2'] = a_tok
            a_tok -= len(a)
            new_op['a1'] = a_tok
            new_op['b1'] = b_tok
            new_op['b2'] = b_tok
            new_op['tokens'] = a
            ops.append(new_op)
            x -= 1
        elif lengths[x][y] == lengths[x][y-1]:
            b = b_lines[y-1]
            new_op = {}
            new_op['name'] = 'insert'
            new_op['b2'] = b_tok
            b_tok -= len(b)
            new_op['b1'] = b_tok
            new_op['a1'] = a_tok
            new_op['a2'] = a_tok
            new_op['tokens'] = b
            y -= 1
            ops.append(new_op)
        else:
            a = a_lines[x-1]
            b = b_lines[y-1]
            a_tok -= len(a)
            b_tok -= len(b)
           # print(x, y)
            for new_op in matching_res[x-1][y-1]:
             #   print(new_op)
                new_op['a1'] += a_tok
                new_op['a2'] += a_tok
                new_op['b1'] += b_tok
                new_op['b2'] += b_tok
                ops.append(new_op)
            x -= 1
            y -= 1

    for a in a_lines[:x][::-1]:
        new_op = {}
        new_op['name'] = 'delete'
        new_op['a2'] = a_tok
        a_tok -= len(a)
        new_op['a1'] = a_tok
        new_op['b1'] = b_tok
        new_op['b2'] = b_tok
        new_op['tokens'] = a
        ops.append(new_op)
    for b in b_lines[:y][::-1]:
        new_op = {}
        new_op['name'] = 'insert'
        new_op['b2'] = b_tok
        b_tok -= len(b)
        new_op['b1'] = b_tok
        new_op['a1'] = a_tok
        new_op['a2'] = a_tok
        new_op['tokens'] = b
        ops.append(new_op)
    return ops 

def matched(x, y):
    new_op = {}
    new_op['name'] = 'equal'
    new_op['a1'] = 0
    new_op['a2'] = len(x)
    new_op['b1'] = 0
    new_op['b2'] = len(y)
    return [new_op]

def diff(cont_a, cont_b):
    a_lines = [text_split.tokenize('\n' + x) for x in cont_a.splitlines() if not(x == '')]
    b_lines = [text_split.tokenize('\n' + x) for x in cont_b.splitlines() if not(x == '')]
    
    lengths = [[0 for j in range(len(b_lines)+1)] for i in range(len(a_lines)+1)]
    matching_res = defaultdict(dict)
    
    matched_x = {}
    matched_y = {}
    cnt = defaultdict(int)
    for i, x in enumerate(a_lines):
        cnt[''.join(x)] += 1

    
    for i, x in enumerate(a_lines):
        matched_x[i] = False
        if cnt[''.join(x)] > 1: 
           continue
        for j, y in enumerate(b_lines):
            if ''.join(x) == ''.join(y) and j not in matched_y:
                matching_res[i][j] = matched(x, y)
                matched_x[i] = True
                matched_y[j] = True
                break
                
    for i, x in enumerate(a_lines):
        for j, y in enumerate(b_lines):
            if (j not in matched_y) and not(matched_x[i]):
                matching_res[i][j] = match(x, y)
            if j in matching_res[i] and not(matching_res[i][j] == None):
                lengths[i+1][j+1] = lengths[i][j] + 1
            else:
                lengths[i+1][j+1] = max(lengths[i+1][j], lengths[i][j+1])
    # read the substring out from the matrix
    ops = []
    x, y = len(a_lines), len(b_lines)
    a_tok = sum([len(a) for a in a_lines])
    b_tok = sum([len(b) for b in b_lines])

    while x != 0 and y != 0:

        if lengths[x][y] == lengths[x-1][y]:
            a = a_lines[x-1]
            new_op = {}
            new_op['name'] = 'delete'
            new_op['a2'] = a_tok
            a_tok -= len(a)
            new_op['a1'] = a_tok
            new_op['b1'] = b_tok
            new_op['b2'] = b_tok
            new_op['tokens'] = a
            ops.append(new_op)
            x -= 1
        elif lengths[x][y] == lengths[x][y-1]:
            b = b_lines[y-1]
            new_op = {}
            new_op['name'] = 'insert'
            new_op['b2'] = b_tok
            b_tok -= len(b)
            new_op['b1'] = b_tok
            new_op['a1'] = a_tok
            new_op['a2'] = a_tok
            new_op['tokens'] = b
            y -= 1
            ops.append(new_op)
        else:
            a = a_lines[x-1]
            b = b_lines[y-1]
            a_tok -= len(a)
            b_tok -= len(b)
            for new_op in matching_res[x-1][y-1]:
                new_op['a1'] += a_tok
                new_op['a2'] += a_tok
                new_op['b1'] += b_tok
                new_op['b2'] += b_tok
                ops.append(new_op)
            x -= 1
            y -= 1

    for a in a_lines[:x][::-1]:
        new_op = {}
        new_op['name'] = 'delete'
        new_op['a2'] = a_tok
        a_tok -= len(a)
        new_op['a1'] = a_tok
        new_op['b1'] = b_tok
        new_op['b2'] = b_tok
        new_op['tokens'] = a
        ops.append(new_op)
    for b in b_lines[:y][::-1]:
        new_op = {}
        new_op['name'] = 'insert'
        new_op['b2'] = b_tok
        b_tok -= len(b)
        new_op['b1'] = b_tok
        new_op['a1'] = a_tok
        new_op['a2'] = a_tok
        new_op['tokens'] = b
        ops.append(new_op)
    return combined(ops)
"""
