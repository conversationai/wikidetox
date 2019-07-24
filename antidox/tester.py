""" Program that's gets the latest revisions from a custom mediawiki (without the use of an SSE client) and checks for PII and toxicity.
    Note: Must create custom family for writing to personal wikibot. See antidox README.md file"""
import argparse
import json
import os
import time
import datetime
import requests
import pywikibot
from antidox import clean
from antidox import perspective


def wiki_write(result, header):
  """ Writes results to wikipedia/wikimedia bot page """
  pywikibot.config.register_family_file('doxwiki', os.path.join(os.path.dirname(__file__), 'doxwiki_family.py'))
  pywikibot.config.usernames['doxwiki']['en'] = u'Antidoxer'
  site = pywikibot.Site()
  repo = site.data_repository()
  page = pywikibot.Page(site, u"User_talk:Antidoxer")

  heading = (header)
  content = (result)
  message = "\n\n{}\n{} --~~~~".format(heading, content)
  page.save(summary="Testing", watch=None, minor=False, botflag=True,
            force=False, async=False, callback=None,
            apply_cosmetic_changes=None, appendtext=message)

def log_change():
  """ gets latest revisions and cleans them """
  apikey_data, toxicity, dlp = perspective.get_client()
  start = datetime.datetime.utcnow() - datetime.timedelta(minutes=2)
  while True:
    end = datetime.datetime.utcnow()
    page = (args.mediawiki + "api.php?action=query&list=recentchanges&rclimit=500&rcprop=title%7Cids%7Csizes%7Cflags%7Cuser&rcdir=newer&rcstart="+ start.isoformat() + "&rcend=" + end.isoformat() + "&format=json")
    get_page = requests.get(page)
    response = json.loads(get_page.content)
    start = end
    for change in response['query']['recentchanges']:
      print('new change:')
      revid = str(change['revid'])
      old_revid = str(change['old_revid'])
      compare = (args.mediawiki + "api.php?action=compare&fromrev="
                 + old_revid + "&torev=" + revid + "&format=json")
      get_compare = requests.get(compare)
      response = json.loads(get_compare.content.decode('utf-8'))

      if 'compare' not in response:
        continue
      revision = response['compare']['*']
      text = clean.content_clean(revision)
      dlp_response = perspective.dlp_request(dlp, apikey_data, text)
      print(text)
      try:
        perspective_response = perspective.perspective_request(toxicity, text)
      # Perspective can't handle language errors at this time
      except google_api_errors.HttpError as err:
        print('Error:', err)
        return
      has_pii_bool, pii_type = perspective.contains_pii(dlp_response)
      if has_pii_bool:
        header = '==Possible Doxxing Detected: Waiting for review=='
        result = (json.dumps({u"comment_text":text, "contains_pii": True, "pii_type":pii_type})+"\n")
        wiki_write(result, header)

      if perspective.contains_toxicity(perspective_response):
        header = '==Possibly Toxic Detected: Waiting for review=='
        result = (json.dumps({u"comment_text":text, "contains_toxicity": True,
                              "summaryScore":perspective_response['attributeScores']
                                             ['TOXICITY']['summaryScore']['value']})+"\n")
        wiki_write(result, header)
      time.sleep(120)


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--mediawiki', help='pathway to fake http://sorenj02.nyc.corp.google.com/mediawiki/')
  parser.add_argument('--wikipedia', help='pathway to wikipedia:https://en.wikipedia.org/w ')
  args = parser.parse_args()
  log_change()
