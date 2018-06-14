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
