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

wikipedia_revisions_ingester.

Read in Wikipedia raw revisions output them to stdout in json format.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import subprocess
import xml.sax
from . import xml_path
import argparse



TALK_PAGE_NAMESPACE = ['1', '3', '5', '7', '9', '11', '13', '15'] 

class ParserContentHandler(xml.sax.ContentHandler):
  """Content handler using a minimal incremental combinator parser."""

  def __init__(self, data_reset_path, data_paths, revision_reset_path):
    xml.sax.ContentHandler.__init__(self)
    # The path through the XML to get to where we currently are.
    self.xml_path = xml_path.XmlPath()
    self.data = {}
    self.data_reset_path = data_reset_path
    self.data_paths = data_paths
    self.revision_reset_path = revision_reset_path
    self.page_data = {}

  def startElement(self, name, attrs):
    self.xml_path.enter(name)

  def endElement(self, name):
    # TODO(nthain): Wrap the inside of the top ifs in a try-catch
    # to determine when things go wrong.
    if self.xml_path.element_path_eq(self.revision_reset_path):
      if 'user_ip' in self.data:
         self.data['user_id'] = -1
         self.data['user_text'] = self.data['user_ip']
      self.data['page_id'] = self.page_data['page_id']
      self.data['page_namespace'] = self.page_data['page_namespace']
      self.data['page_title'] = self.page_data['page_title']
      if not('text' in self.data):
         self.data['text'] = ""
      if not('user_id' in self.data):
         self.data['user_id'] = None
         self.data['user_text'] = None
      if self.data['page_namespace'] in TALK_PAGE_NAMESPACE:
        print(json.dumps(self.data))
      self.data = {} 
       
    if self.xml_path.element_path_eq(self.data_reset_path):
      self.page_data = {}

    self.xml_path.exit()

  def characters(self, content_text):
    self.xml_path.add_line_of_content()
    for data_name, data_path in self.data_paths:
      if self.xml_path.element_path_eq(data_path):
        if 'page' in data_name:
          if data_name not in self.page_data:
            self.page_data[data_name] = ""
          self.page_data[data_name] += content_text
        else:
          if data_name not in self.data:
            self.data[data_name] = ""
          self.data[data_name] += content_text

def _get_paths():
  data_reset_path = xml_path.XmlPath().enter_many(['mediawiki', 'page'])
  revision_reset_path = xml_path.XmlPath().enter_many(['mediawiki', 'page', 'revision']) 
  data_paths = [
      ('comment', xml_path.XmlPath().enter_many(
          ['mediawiki', 'page', 'revision', 'comment'])),
      ('format', xml_path.XmlPath().enter_many(
          ['mediawiki', 'page', 'revision', 'format'])),
      ('model', xml_path.XmlPath().enter_many(
          ['mediawiki', 'page', 'revision', 'model'])),
      ('page_id', xml_path.XmlPath().enter_many(['mediawiki', 'page', 'id'])),
      ('page_namespace',
       xml_path.XmlPath().enter_many(['mediawiki', 'page', 'ns'])),
      ('page_title',
       xml_path.XmlPath().enter_many(['mediawiki', 'page', 'title'])),
      ('rev_id',
       xml_path.XmlPath().enter_many(['mediawiki', 'page', 'revision', 'id'])),
      ('timestamp', xml_path.XmlPath().enter_many(
          ['mediawiki', 'page', 'revision', 'timestamp'])),
      ('sha1', xml_path.XmlPath().enter_many(
          ['mediawiki', 'page', 'revision', 'sha1'])),
      ('text', xml_path.XmlPath().enter_many(
          ['mediawiki', 'page', 'revision', 'text'])),
      ('user_id', xml_path.XmlPath().enter_many(
          ['mediawiki', 'page', 'revision', 'contributor', 'id'])),
      ('user_text', xml_path.XmlPath().enter_many(
          ['mediawiki', 'page', 'revision', 'contributor', 'username'])),
      ('user_ip', xml_path.XmlPath().enter_many(
          ['mediawiki', 'page', 'revision', 'contributor', 'ip'])),

  ]
  return data_reset_path, revision_reset_path, data_paths

def parse_stream(input_file):
  data_reset_path, revision_reset_path, data_paths = _get_paths()
  content_handler = ParserContentHandler(
    data_reset_path=data_reset_path, 
    data_paths=data_paths, 
    revision_reset_path=revision_reset_path)

  cmd = (['7z', 'x', input_file, '-so']
       if input_file.endswith('.7z') else ['cat', input_file])
  p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
  xml.sax.parse(p.stdout, content_handler)
