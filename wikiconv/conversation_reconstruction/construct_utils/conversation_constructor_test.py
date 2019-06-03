"""Tests for ReconstructConversation."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import unittest

from wikiconv.conversation_reconstruction.construct_utils import conversation_constructor


class ConversationContructorTest(unittest.TestCase):

  def test_conversation_constructor(self):
    processor = conversation_constructor.ConversationConstructor()
    page_state = []
    latest_content = []
    rev = {
        "user_id": 8083618,
        "format": "placeholder",
        "user_text": "Anders Torlind",
        "timestamp": "2001-09-11T18:22:34Z",
        "text": "YIKES!  I came here from the [[Prostitution]] page",
        "page_title": "placeholder",
        "page_id": 28031,
        "rev_id": 332251982
    }
    (new_page_state, actions,
     new_rev) = processor.process(page_state, latest_content, rev)
    self.maxDiff = 30000  # pylint: disable=invalid-name
    self.assertEqual(
        new_page_state, {
            u"deleted_comments": [],
            u"timestamp": "2001-09-11T18:22:34Z",
            u"page_state": {
                u"page_title": "placeholder",
                u"page_id": 28031,
                u"actions": {
                    0: ("332251982.0.0", 0),
                    51: (-1, -1)
                }
            },
            u"authors": {
                "332251982.0.0": [(8083618, "Anders Torlind")]
            },
            u"conversation_id": {
                "332251982.0.0": "332251982.0.0"
            },
            u"page_id": 28031,
            u"ancestor_id": {
                "332251982.0.0": "332251982.0.0"
            },
            u"rev_id": 332251982
        })
    self.assertEqual(new_rev,
                     u"YIKES!  I came here from the [[Prostitution]] page\n")
    self.assertEqual(actions, [{
        "user_id":
            8083618,
        u"cleaned_content":
            u"YIKES!  I came here from the [[Prostitution]] page\n",
        "user_text":
            "Anders Torlind",
        "timestamp":
            "2001-09-11T18:22:34Z",
        "content":
            u"YIKES!  I came here from the [[Prostitution]] page\n",
        "parent_id":
            None,
        "replyTo_id":
            None,
        u"page_id":
            28031,
        "indentation":
            0,
        u"authors": [(8083618, "Anders Torlind")],
        u"conversation_id":
            "332251982.0.0",
        u"page_title":
            "placeholder",
        "type":
            "ADDITION",
        "id":
            "332251982.0.0",
        u"ancestor_id":
            "332251982.0.0",
        "rev_id":
            332251982
    }])


if __name__ == "__main__":
  unittest.main()
