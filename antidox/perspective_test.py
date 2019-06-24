# -*- coding: utf-8 -*-

from antidox import perspective
import unittest
import sys
if sys.version_info >= (3, 3):
    from unittest import mock
else:
    import mock

class TestPerspective(unittest.TestCase):

  def test_contains_pii_true(self):
    dlp_response = \
		{
		  "result": {
		    "findings": [
		      {
		        "quote": "footfungusinbellybutton@gmail.com",
		        "infoType": {
		          "name": "EMAIL_ADDRESS"
		        },
		        "likelihood": "LIKELY",
		        "location": {
		          "byteRange": {
		            "start": "13",
		            "end": "46"
		          },
		          "codepointRange": {
		            "start": "13",
		            "end": "46"
		          }
		        },
		        "createTime": "2019-05-31T21:23:12.402Z"
		      },
		      {
		        "quote": "(206) 555-0123",
		        "infoType": {
		          "name": "PHONE_NUMBER"
		        },
		        "likelihood": "LIKELY",
		        "location": {
		          "byteRange": {
		            "start": "67",
		            "end": "81"
		          },
		          "codepointRange": {
		            "start": "67",
		            "end": "81"
		          }
		        },
		        "createTime": "2019-05-31T21:23:12.402Z"
		      }
		    ]
		  }
		}
    has_pii = perspective.contains_pii(dlp_response)
    self.assertTrue(has_pii)

  def test_contains_pii_false(self):
    dlp_response = \
      {
        "result": {}
      }
    has_pii = perspective.contains_pii(dlp_response)
    self.assertEqual(has_pii, (False, None))

  def test_contains_toxicity_true(self):
    perspective_response = \
    {
    "attributeScores": {
      "INSULT": {
        "spanScores": [
          {
            "begin": 0,
            "end": 14,
            "score": {
              "value": 0.8521307,
              "type": "PROBABILITY"
            }
          }
        ],
        "summaryScore": {
          "value": 0.8521307,
          "type": "PROBABILITY"
        }
      },
      "TOXICITY": {
        "spanScores": [
          {
            "begin": 0,
            "end": 14,
            "score": {
              "value": 0.96624386,
              "type": "PROBABILITY"
            }
          }
        ],
        "summaryScore": {
          "value": 0.96624386,
          "type": "PROBABILITY"
        }
      },
      "THREAT": {
        "spanScores": [
          {
            "begin": 0,
            "end": 14,
            "score": {
              "value": 0.39998722,
              "type": "PROBABILITY"
            }
          }
        ],
        "summaryScore": {
          "value": 0.39998722,
          "type": "PROBABILITY"
        }
      }
    },
    "languages": [
      "en"
    ],
    "detectedLanguages": [
      "en"
    ]
  }
    is_toxic = perspective.contains_toxicity(perspective_response)
    self.assertTrue(is_toxic)

  def test_contains_toxicity_false(self):
    perspective_response = \
    {
    "attributeScores": {
      "THREAT": {
        "spanScores": [
          {
            "begin": 0,
            "end": 35,
            "score": {
              "value": 0.09605787,
              "type": "PROBABILITY"
            }
          }
        ],
        "summaryScore": {
          "value": 0.09605787,
          "type": "PROBABILITY"
        }
      },
      "INSULT": {
        "spanScores": [
          {
            "begin": 0,
            "end": 35,
            "score": {
              "value": 0.07253261,
              "type": "PROBABILITY"
            }
          }
        ],
        "summaryScore": {
          "value": 0.07253261,
          "type": "PROBABILITY"
        }
      },
      "TOXICITY": {
        "spanScores": [
          {
            "begin": 0,
            "end": 35,
            "score": {
              "value": 0.072236896,
              "type": "PROBABILITY"
            }
          }
        ],
        "summaryScore": {
          "value": 0.072236896,
          "type": "PROBABILITY"
        }
      }
    },
    "languages": [
      "en"
    ],
    "detectedLanguages": [
      "en"
    ]
    }
    is_toxic = perspective.contains_toxicity(perspective_response)
    self.assertFalse(is_toxic)
  def test_get_wikipage(self):
    wiki_response = \
    u"""{{talkheader|wp=yes|WT:NYC|WT:WPNYC}}
{{WPBS|1=
{{WikiProject Cities|class=project|importance=na}}
{{WikiProject New York City|class=project|importance=na}}
{{WikiProject New York|class=project|importance=na}}
{{WikiProject United States|class=project|importance=na}}
}}
{{Wikipedia:Wikipedia Signpost/WikiProject used|link=Wikipedia:Wikipedia Signpost/2012-12-31/WikiProject report|writer= [[User:Mabeenot|Mabeenot]]| ||day =31|month=December|year=2012}}
{{auto archiving notice|bot=MiszaBot II|botlink=User:MiszaBot II|age=60}}{{User:MiszaBot/config
|archiveheader = {{talkarchivenav}}
|maxarchivesize = 100K
|counter = 7
|minthreadsleft = 5
|minthreadstoarchive = 1
|algo = old(60d)
|archive = Wikipedia talk:WikiProject New York City/Archive %(counter)d
}}{{User:HBC Archive Indexerbot/OptIn|target=Wikipedia talk:WikiProject New York City/Archive index|mask=Wikipedia talk:WikiProject New York City/Archive <#>|leading_zeros=0|indexhere=no}}

{{TOC right}}

== Help with a park article? ==

Hi! I didn't know if anyone was willing to work on a park article or not - a student of mine created the article on [[St. James Park (Bronx)]]. The class ends this week and I'm not entirely sure if they will be back on to edit it, but at the present it lacks information and sourcing to establish how it's notable. I'm going to try to do as much as I can for it, but I'm admittedly kind of swamped with other classes so I wanted to see if anyone would be interested in this. 15:36, 7 May 2019 (UTC)

== Wikipedia:Naming conventions (US stations)/NYC Subway RfC ==

Just so everyone who would come here knows, there is an ongoing RfC at [[Wikipedia:Naming conventions (US stations)/NYC Subway RfC]] that WP:NYC might be interested in. {{sbb}} --<span style="border:1px solid #ffa500;background:#f3dddd;">&nbsp;[[User:I dream of horses|I dream of horses]]&nbsp;</span><span style="border:1px solid #ffa500">{{small|&nbsp;If you reply here, please [[WP:ECHO|ping me]] by adding <nowiki>{{U|I dream of horses}}</nowiki> to your message&nbsp;}}</span>  {{small|([[User talk:I dream of horses|talk to me]]) ([[Special:Contributions/I dream of horses|My edits]])}} @  05:11, 12 June 2019 (UTC)"""
    clean_text = \
    u"""Help with a park article? 

Hi! I didn't know if anyone was willing to work on a park article or not - a student of mine created the article on St. James Park (Bronx). The class ends this week and I'm not entirely sure if they will be back on to edit it, but at the present it lacks information and sourcing to establish how it's notable. I'm going to try to do as much as I can for it, but I'm admittedly kind of swamped with other classes so I wanted to see if anyone would be interested in this. 

 Wikipedia:Naming conventions (US stations)/NYC Subway RfC 

Just so everyone who would come here knows, there is an ongoing RfC at Wikipedia:Naming conventions (US stations)/NYC Subway RfC that WP:NYC might be interested in.       @  """
    text = perspective.wiki_clean(wiki_response)
    self.assertEqual(text.strip(), clean_text.strip())


class Test_BigQuery(unittest.TestCase):

  def test_use_query(self):
    fake_response_comments = [
      {'cleaned_content': 'comment1'},
      {'cleaned_content': 'comment2'}
    ]
    not_big_q = mock.Mock()
    mock_query_job = mock.Mock()
    mock_query_job.result = mock.Mock(return_value=fake_response_comments)
    not_big_q.query = mock.Mock(return_value=mock_query_job)
    rows = perspective.use_query('cleaned_content', """SELECT 'cleaned_content' FROM 'fakeproject.fakedatbase.fakedataset' """, not_big_q)
    self.assertEqual(type(rows[0]), str)
    self.assertEqual(len(rows), len(fake_response_comments))
  

if __name__ == '__main__':
    unittest.main()
