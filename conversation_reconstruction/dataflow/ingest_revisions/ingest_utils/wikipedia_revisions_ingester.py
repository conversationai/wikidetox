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

Wikipedia Revisions Ingester

Read in Wikipedia raw revisions output them to stdout in json format.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
from lxml import etree
import StringIO


TALK_PAGE_NAMESPACE = ['1', '3', '5', '7', '9', '11', '13', '15', "101", "109", "119", "447", "711", "829", "2301", "2303"] 
revision_values = {'comment': 'comment', 'format': 'format', 'model': 'model', 'id': 'rev_id', 'timestamp': 'timestamp', 'sha1': 'sha1', 'text': 'text'}
contributor_values = {'id': 'user_id', 'username': 'user_text', 'ip': 'user_ip'}
page_data_mapping = {"ns": "namespace", "id": "id", "title": "title"}

def process_revision(namespace_length, rev):
    ret = {}
    for k in contributor_values.keys():
        ret[k] = None
    for k in revision_values.keys():
        ret[k] = None
    for ele in rev.iter():
        parent = ele.getparent().tag[namespace_length:]
        if parent == "revision":
           if ele.tag[namespace_length:] in revision_values.keys():
              ret[revision_values[ele.tag[namespace_length:]]] = ele.text
        if parent == "contributor":
           if ele.tag[namespace_length:] in contributor_values.keys():
              ret[contributor_values[ele.tag[namespace_length:]]] = ele.text
    return ret

def parse_stream(input_file):
  context = etree.iterparse(input_file, events=('end', 'start', ), tag=('{*}page', '{*}ns', '{*}title', '{*}id', '{*}revision'))
  page_data = {}
  rev_data = {}
  route = []
  for event, ele in context:
      namespace_length = ele.tag.find("}")+1
      if event == 'start':
         route.append(ele.tag[namespace_length:])
         continue
      route.pop()
      if ele.tag[namespace_length:] == "page":
         page_data = {}
      if ele.tag[namespace_length:] in ["ns", "id", "title"] and route[-1] == "page":
         page_data[page_data_mapping[ele.tag[namespace_length:]]] = ele.text
      if "namespace" in page_data and "revision" in ele.tag: #  and page_data["namespace"] in TALK_PAGE_NAMESPACE
         rev_data = process_revision(namespace_length, ele)
         for page_data_name in page_data_mapping.values():
             if page_data_name in page_data:
                rev_data['page_%s'%page_data_name] = page_data[page_data_name]
             else:
                rev_data['page_%s'%page_data_name] = None
         yield rev_data
         rev_data = {}
      ele.clear()
      while ele.getprevious() is not None:
          del ele.getparent()[0]
  del context

if __name__ == "__main__":
#   parse_stream("testdata/gigantic_xml.xml")
   for x in parse_stream("testdata/gigantic_xml.xml"):
       pass
