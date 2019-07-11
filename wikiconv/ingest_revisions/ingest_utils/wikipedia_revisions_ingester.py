"""Copyright 2017 Google Inc. Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.

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
import hashlib

TALK_PAGE_NAMESPACE = [
    '1', '3', '5', '7', '9', '11', '13', '15', '101', '109', '119', '447',
    '711', '829', '2301', '2303'
]
FIELDS = [
    'comment', 'format', 'model', 'rev_id', 'timestamp', 'sha1', 'text',
    'user_id', 'user_text', 'page_id', 'page_title', 'page_namespace'
]


def process_revision(namespace_length, rev):
  """Extracts information from individual revision."""
  ret = {f: None for f in FIELDS}
  for ele in rev.iter():
    parent = ele.getparent().tag[namespace_length:]
    tag = ele.tag[namespace_length:]
    if parent == 'revision' and tag in [
        'comment', 'format', 'model', 'id', 'timestamp', 'sha1', 'text'
    ]:
      if tag == 'id':
        ret['rev_id'] = ele.text
      else:
        ret[tag] = ele.text
    elif parent == 'contributor' and tag in ['id', 'username', 'ip']:
      if (tag == 'username' or tag == 'ip'):
        ret['user_text'] = ele.text
      else:
        ret['user_' + tag] = ele.text
  return ret


def clearup(ele):
  """
    Clears up used memory from:
       1) the content in the current the tag;
       2) the reference links from siblings to the current tag.
    """
  ele.clear()  # utility of this : two ceonsecutive large ones
  while ele.getprevious() is not None:
    del ele.getparent()[0]


def parse_stream(input_file):
  """Iteratively parses XML file into json records. Clears up memory after processing each element to avoid large revisions/pages taking up memories.

  Variables:
      STRING: page_id, page_title, page_namespace, tag
      DICTIONARY: rev_data
      INTEGER: namespace_length
  """
  context = etree.iterparse(
      input_file,
      events=('end',),
      tag=('{*}page', '{*}ns', '{*}title', '{*}id', '{*}revision'),
      huge_tree=True)
  page_id = None
  page_title = None
  page_namespace = None
  rev_data = {}
  for event, ele in context:
    namespace_length = ele.tag.find('}') + 1
    tag = ele.tag[namespace_length:]
    parent = ele.getparent().tag[namespace_length:]
    if tag == 'page':
      page_id = None
      page_title = None
      page_namespace = None
      clearup(ele)
    elif tag == 'ns' and parent == 'page':
      page_namespace = ele.text
      clearup(ele)
    elif tag == 'id' and parent == 'page':
      page_id = ele.text
      clearup(ele)
    elif tag == 'title' and parent == 'page':
      page_title = ele.text
      clearup(ele)
    elif tag == 'revision':
      if page_namespace is not None and page_namespace in TALK_PAGE_NAMESPACE:
        rev_data = process_revision(namespace_length, ele)
        rev_data.update({
            'page_title': page_title,
            'page_id': page_id,
            'page_namespace': page_namespace
        })
        yield rev_data
        rev_data = {}
      clearup(ele)


if __name__ == '__main__':
  for x in parse_stream(
      open('../enwiki-20180501-pages-meta-history8.xml-p1444867p1470135', 'r')):
    print(x['rev_id'])
