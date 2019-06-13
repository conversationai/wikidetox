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
    clean_text = \
    """ Grant Square geographic anomaly 
    The commons description of Grant Square in Brooklyn describes it as being at Bedford and Rogers Avenues between Dean and Bergen Streets in Crown Heights.  However, the Washington Temple Church of God in Christ (former Loew's Theater) is on the northwest corner of Bergen Street and Bedford Avenue which is said to be in Bedford-Stuyvesant, yet it's directly across Bedford Avenue from the "Grant Gore." So wouldn't that mean Grant Square is in both Bed-Stuy ''and'' Crown Heights? I need to know this, because I took a bunch of pictures of both sites back in October 2018. -   
    Well:
    As I'm sure you know, neighborhood boundaries in NYC aren't officially set, they are determined by usage;
    Google Maps shows the boundary between Bed-Stuy and Crown Heights at Atlantic Avenue, a few blocks north of Grant Square, putting the square in Crown Heights;
    ''The Encyclopedia of New York City'' lists the same boundary as Google Maps;
    However, ''The Neighborhoods of Brooklyn'' shows the boundary at Park Place, putting the square (just) in Bed-Stuy;
    Then again, the ''AIA Guide to New York City'' uses the Atlantic Avenue border;
    The NYCLPC's Crown Heights North Historic District has a northern boundary which is midblock south of Atlantic Avenue, meaning it, too, recognizes those blocks as being part of Crown Heights. (Grant Square itself is not part of the district, but the building at the southeast corner of Dean and Rogers, confusingly called the "Fort Greene Grant Square Center", even though it's nowhere near Fort Greene, is in the district);
    The website of the Washington Temple Church of God in Christ says it is "Located in the Crown Heights section of Brooklyn".
    All-in-all, the usage appears to be very much on the side of Grant Square being in Crown Heights and not in Bed-Stuy - which brings up the question, where did you see the C.O.G.I.C described as being in Bed-Stuy?   
    JimHenderson's picture of the church. I have two of my own coming. Do you know what else I noticed? Google Maps also shows the western border of Crown Heights as being along Washington Avenue, which would place ''both'' Studebaker Buildings (Bedford Avenue and Sterling Place, as well as Dean Street) as being in Crown Heights! -   
     Jim often takes his photos while on group bicycle rides, maybe he didn't realize he had crossed over a neighborhood boundary.The NYCLPC clearly describes the Studebaker Building on Bedford as in Crown Heights.  The other one isn't a landmark, but a lot of sites describe it as being in Crown Heights as well   and by the definitions of pretty most all of the sources above too.  It's really too far south to be in Bed-Stuy, so I wonder why that designation got started?   
    I believe it was the former Franklin Shuttle Station next door. Well, since both are officially in Crown Heights, we really need better names for both of them now.    
     I shan’t claim to know; sometimes I’m not even sure whether I’ve crossed into Queens.   
     Don't you see the "You are now leaving Brooklyn - Fugeddabouddit" signs?   
     In his defense, those signs can't be at every street that crosses the Brooklyn-Queens line. As far as the Studebaker Buildings, since both are officially considered to be in Crown Heights, how about renaming the gallery for the landmark "Studebaker Building (Bedford Avenue, Brooklyn)," and I'll rename the other one "Studebaker Building (Dean Street, Brooklyn)?" I'll even correct Dean Street (BMT Franklin Avenue Line).-   

    Buzz Aldrin in project scope?
    Why would Buzz Aldrin be in  scope?    
    No idea. I've removed it.   
     WP 1.0 Bot Beta 
    Error: <HttpError 400 when requesting https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze?key=AIzaSyA5kva-B5eLUBMD-VB426Pan3AlPXzWOXc&alt=json returned "Attribute THREAT does not support request languages: hu">

    Hello! Your WikiProject has been selected to participate in the WP 1.0 Bot rewrite beta. This means that, starting in the next few days or weeks, your assessment tables will be updated using code in the new bot, codenamed Lucky. You can read more about this change on the Wikipedia 1.0 Editorial team page. Thanks!   

     A new newsletter directory is out! 

    A new '''Newsletter directory''' has been created to replace the old, out-of-date one. If your WikiProject and its taskforces have newsletters (even inactive ones), or if you know of a missing newsletter (including from sister projects like WikiSpecies), please include it in the directory! The template can be a bit tricky, so if you need help, just post the newsletter on the template's talk page and someone will add it for you.
    – Sent on behalf of . 

     Help with a park article? 

    Hi! I didn't know if anyone was willing to work on a park article or not - a student of mine created the article on St. James Park (Bronx). The class ends this week and I'm not entirely sure if they will be back on to edit it, but at the present it lacks information and sourcing to establish how it's notable. I'm going to try to do as much as I can for it, but I'm admittedly kind of swamped with other classes so I wanted to see if anyone would be interested in this. 

     Wikipedia:Naming conventions (US stations)/NYC Subway RfC 

    Just so everyone who would come here knows, there is an ongoing RfC at Wikipedia:Naming conventions (US stations)/NYC Subway RfC that WP:NYC might be interested in.       @  """
    text = perspective.get_wikipage("Wikipedia_talk:WikiProject_New_York_City")
    self.assertTrue(text, clean_text)



if __name__ == '__main__':
    unittest.main()
