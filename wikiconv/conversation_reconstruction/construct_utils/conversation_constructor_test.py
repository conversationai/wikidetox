"""Tests for ReconstructConversation."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import unittest

from construct_utils import conversation_constructor


class ConversationContructorTest(unittest.TestCase):

  def test_conversation_constructor(self):
    processor = conversation_constructor.Conversation_Constructor()
    page_state = []
    latest_content = []
    rev = {
        "comment": "*",
        "sha1": "cb40d5f5b69538788c2f726822565f9a53e4452c",
        "user_id": 8083618,
        "format": "placeholder",
        "user_text": "Anders Torlind",
        "timestamp": "2001-09-11T18:22:34Z",
        "contentformat": "text/x-wiki",
        "user_ip": "placeholder",
        "contentmodel": "wikitext",
        "text":
            "YIKES!  I came here from the [[Prostitution]] page - surely we "
            "have to qualify the 'for reproduction' part of the statement if "
            "it's linked to prostitution!  And what about all those - ahem - "
            "other activities.  Not to mention homosexuality.  If we keep this"
            " definition the way it is, prostitution should link to something "
            "else!\n\nSeems to serve perfectly fine for that at least, "
            "although it DOES need some more content (notably homesexual "
            "intercourse). Feel free to add! :-) (oh, and by the way, it's dry"
            " and factual on purpose, in order to avoid bias)---Anders "
            "T\u00f6rlind\n\nWell, it's exactly that kind of attitude that had"
            " some people wondering what Bill Cllinton actually MEANT by "
            "sexual contact! --MichaelTinkler\n\nI'm sorry that i have "
            "offended you, although i know not what i have done. Please accept"
            " my aplogies. --Anders T\u00f6rlind",
        "parentid": 331924041,
        "page_title": "placeholder",
        "model": "placeholder",
        "page_namespace": "placeholder",
        "page_id": 28031,
        "rev_id": 332251982
    }
    (new_page_state, actions,
     new_rev) = processor.process(page_state, latest_content, rev)
    self.assertEqual(
        new_page_state, {
            u"deleted_comments": [],
            u"timestamp": "2001-09-11T18:22:34Z",
            u"page_state": {
                u"page_title": "placeholder",
                u"page_id": 28031,
                u"actions": {
                    0: ("332251982.0.0", 0),
                    837: (-1, -1)
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
    self.assertEqual(
        new_rev,
        u"YIKES!  I came here from the [[Prostitution]] page - surely we have to qualify the 'for reproduction' part of the statement if it's linked to prostitution!  And what about all those - ahem - other activities.  Not to mention homosexuality.  If we keep this definition the way it is, prostitution should link to something else!\nSeems to serve perfectly fine for that at least, although it DOES need some more content (notably homesexual intercourse). Feel free to add! :-) (oh, and by the way, it's dry and factual on purpose, in order to avoid bias)---Anders T\\u00f6rlind\nWell, it's exactly that kind of attitude that had some people wondering what Bill Cllinton actually MEANT by sexual contact! --MichaelTinkler\nI'm sorry that i have offended you, although i know not what i have done. Please accept my aplogies. --Anders T\\u00f6rlind\n"
    )
    self.assertEqual(actions, [{
        "user_id":
            8083618,
        u"cleaned_content":
            u"YIKES!  I came here from the [[Prostitution]] page - surely we have to qualify the 'for reproduction' part of the statement if it's linked to prostitution!  And what about all those - ahem - other activities.  Not to mention homosexuality.  If we keep this definition the way it is, prostitution should link to something else!\nSeems to serve perfectly fine for that at least, although it DOES need some more content (notably homesexual intercourse). Feel free to add! -) (oh, and by the way, it's dry and factual on purpose, in order to avoid bias)-Anders T\\u00f6rlind\nWell, it's exactly that kind of attitude that had some people wondering what Bill Cllinton actually MEANT by sexual contact! MichaelTinkler\nI'm sorry that i have offended you, although i know not what i have done. Please accept my aplogies. Anders T\\u00f6rlind\n",
        "user_text":
            "Anders Torlind",
        "timestamp":
            "2001-09-11T18:22:34Z",
        "content":
            u"YIKES!  I came here from the [[Prostitution]] page - surely we have to qualify the 'for reproduction' part of the statement if it's linked to prostitution!  And what about all those - ahem - other activities.  Not to mention homosexuality.  If we keep this definition the way it is, prostitution should link to something else!\nSeems to serve perfectly fine for that at least, although it DOES need some more content (notably homesexual intercourse). Feel free to add! :-) (oh, and by the way, it's dry and factual on purpose, in order to avoid bias)---Anders T\\u00f6rlind\nWell, it's exactly that kind of attitude that had some people wondering what Bill Cllinton actually MEANT by sexual contact! --MichaelTinkler\nI'm sorry that i have offended you, although i know not what i have done. Please accept my aplogies. --Anders T\\u00f6rlind\n",
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
