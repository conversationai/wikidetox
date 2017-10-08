"""A tool to download all wikipedia revisions.

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
from os import path
import urllib2
import argparse

parser = argparse.ArgumentParser(description='Download and save wikipedia revisions from a dump.')
parser.add_argument('--wikidump_url_root', default='https://dumps.wikimedia.org/enwiki/20170601/', help='URL to a wikipedia dump.')
parser.add_argument('--output_dir', default='./tmp', help='Path to save wikipedia files to.')

args = parser.parse_args()

def download_dump(wikidump_url_root, output_dir):

  dumpstatus_url = wikidump_url_root + 'dumpstatus.json'
  response = urllib2.urlopen(dumpstatus_url)
  dumpstatus = json.loads(response.read())
  print(dumpstatus)

  dump_files = dumpstatus['jobs']['metahistory7zdump']['files'].keys()
  dump_files.sort()

  for i, chunk_name in enumerate(dump_files, start=1):
    out_path = path.join(output_dir, chunk_name)
    if path.exists(out_path):
      print('(' + str(i) + ' of ' + str(len(dump_files)) +
            ') skipped, it exists at: ' + out_path)
      continue
    print('(' + str(i) + ' of ' + str(len(dump_files)) + ') downloading: ' +
          out_path)
    chunk_url = wikidump_url_root + chunk_name
    chunk_file = urllib2.urlopen(chunk_url)
    with open(out_path, 'w') as f:
      f.write(chunk_file.read())


if __name__ == '__main__':
  download_dump(args.wikidump_url_root, args.output_dir)