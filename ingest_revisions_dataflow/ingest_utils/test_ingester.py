from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import xml.sax
import subprocess
from os import path
from ingest_utils import wikipedia_revisions_ingester as wiki_ingester

def main():
	
	input_file = path.join('ingest_utils', 'testdata', 'original_example.xml')
	data_reset_path, revision_reset_path, data_paths = wiki_ingester.get_paths()
	content_handler = wiki_ingester.ParserContentHandler(
		data_reset_path=data_reset_path, 
		data_paths=data_paths, 
		revision_reset_path=revision_reset_path)

	cmd = (['7z', 'x', input_file, '-so']
		   if input_file.endswith('.7z') else ['cat', input_file])
	p = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize = 4096)
	xml.sax.parse(p.stdout, content_handler)

if __name__ == '__main__':
	main()