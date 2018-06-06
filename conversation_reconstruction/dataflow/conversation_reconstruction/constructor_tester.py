
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

A dataflow pipeline to reconstruct conversations on Wikipedia talk pages from ingested json files.

Run with:

reconstruct*.sh in helper_shell

"""
from __future__ import absolute_import
import argparse
import logging
import subprocess
import json
from os import path
import urllib2
import traceback
import ast
import copy
import sys

from construct_utils.conversation_constructor import Conversation_Constructor
import requests

def get_revision(page_id):
  baseurl = 'http://en.wikipedia.org/w/api.php'
  ret = []
  props = []
  atts = {'action' : 'query',  'prop' : 'revisions', 'rvprop' : '|'.join(props), 'rvlimit' : 'max', 'format' : 'json', 'pageids' : page_id}
  response = requests.get(baseurl, params = atts)
  data = response.json()
  for rev in 
  while ('continue' in data and 'rvcontinue' in data):
      atts['rvcontinue'] = data['continue']['rvcontinue']
      response = requests.get(baseurl, params = atts)
      data = response.json()


# if (page_id == None) or (page_id == "34948919") or (page_id == "15854766") or (page_id == "32094486"): return

if __name__ == '__main__':

