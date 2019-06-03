import perspective
import unittest

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
    self.assertFalse(has_pii)

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

if __name__ == '__main__':
    unittest.main()
