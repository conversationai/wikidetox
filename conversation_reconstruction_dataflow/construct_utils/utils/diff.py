from __future__ import absolute_import, division, print_function
from builtins import *
from future.builtins.disabled import *

from .tokenizers import text_split
from collections import defaultdict
import copy
import re

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
    if matched_potion >= 1 or (a_len <= 3):
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
 #   print(list(ops))
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
    a_lines = [text_split.tokenize('\n' + x) for x in cont_a.splitlines()]
    b_lines = [text_split.tokenize('\n' + x) for x in cont_b.splitlines()]
    
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
 #   print(list(ops))
    return combined(ops)
