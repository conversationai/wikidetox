"""wikipedia_revisions_ingester.

Read in Wikipedia raw revisions output them to stdout in json format.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import subprocess
import xml.sax
import xml_path
import argparse


parser = argparse.ArgumentParser(description='Download and save wikipedia revisions from a dump.')
parser.add_argument('-i', '--input',  required=True, help='Path to a wikipedia xml or 7z revision dump file.')

args = parser.parse_args()

class ParserContentHandler(xml.sax.ContentHandler):
  """Content handler using a minimal incremental combinator parser."""

  def __init__(self, data_reset_path, data_paths):
    xml.sax.ContentHandler.__init__(self)
    # The path through the XML to get to where we currently are.
    self.xml_path = xml_path.XmlPath()
    self.data = {}
    self.data_reset_path = data_reset_path
    self.data_paths = data_paths

  def startElement(self, name, attrs):
    self.xml_path.enter(name)
    # print('# START: ' + str(self.xml_path))

  def endElement(self, name):
    # print('# END: ' + str(self.xml_path))
    if self.xml_path.element_path_eq(self.data_reset_path):
      print(json.dumps(self.data))
      self.data = {}
    self.xml_path.exit()

  def characters(self, content_text):
    self.xml_path.add_line_of_content()
    for data_name, data_path in self.data_paths:
      if self.xml_path.element_path_eq(data_path):
        if data_name not in self.data:
          self.data[data_name] = ''
        self.data[data_name] += content_text
    # print('# CONTENT: ' + str(self.xml_path))


def main():
  data_reset_path = xml_path.XmlPath().enter_many(['mediawiki', 'page'])
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
      ('rev_timestamp', xml_path.XmlPath().enter_many(
          ['mediawiki', 'page', 'revision', 'timestamp'])),
      ('sha1', xml_path.XmlPath().enter_many(
          ['mediawiki', 'page', 'revision', 'sha1'])),
      ('text', xml_path.XmlPath().enter_many(
          ['mediawiki', 'page', 'revision', 'text'])),
      ('user_id', xml_path.XmlPath().enter_many(
          ['mediawiki', 'page', 'revision', 'contributor', 'id'])),
      ('user_name', xml_path.XmlPath().enter_many(
          ['mediawiki', 'page', 'revision', 'contributor', 'username'])),
  ]
  content_handler = ParserContentHandler(
      data_reset_path=data_reset_path, data_paths=data_paths)

  cmd = (['7z', 'x', args.input, '-so']
         if args.input.endswith('.7z') else ['cat', args.input])
  p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
  xml.sax.parse(p.stdout, content_handler)


if __name__ == '__main__':
  main()