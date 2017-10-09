from conversation_constructor import Conversation_Constructor
import json
import fileinput
import sys
import os
from multiprocessing import Pool
import time
from pathlib import Path

with open('chunks') as fileList:
    for fname in fileList:
        my_file = Path('/scratch/wiki_dumps/conversations/%s' % fname[fname.rindex('/'):-1])
        if not(my_file.exists()):
           print(fname[:-1])
