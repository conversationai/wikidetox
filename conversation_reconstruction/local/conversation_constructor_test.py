"""A simple test for the Conversation_Constructor class.

Run with:
python -m unittest conversation_constructor_test
"""

import os
import json
from unittest import TestCase
from conversation_constructor import Conversation_Constructor

class Conversation_Constructor_Test(TestCase):

	def setUp(self):
		self.constructor = Conversation_Constructor()
		self.test_dir = 'testdata'

	def test_simple_history(self):
		test_file = 'simple_test.json'
		with open(os.path.join(self.test_dir, test_file)) as f:
			history = json.load(f)

		actions_lst = []
		for ind, h in enumerate(history):
		    actions = self.constructor.process(h)
		    for action in actions:
		        actions_lst.append(action)
		        #print(action)

		self.assertEqual('SECTION_CREATION', actions_lst[1]['type'])
		self.assertEqual('COMMENT_ADDING', actions_lst[2]['type'])
		self.assertEqual('COMMENT_ADDING', actions_lst[3]['type'])
		self.assertEqual('COMMENT_MODIFICATION', actions_lst[4]['type'])
		self.assertEqual('COMMENT_REMOVAL', actions_lst[5]['type'])
		self.assertEqual('COMMENT_ADDING', actions_lst[6]['type'])
		self.assertEqual('794724701.29.0', actions_lst[2]['id'])
		self.assertEqual('794724701.29.0', actions_lst[3]['replyTo_id'])
		self.assertEqual('794724701.29.0', actions_lst[6]['replyTo_id'])