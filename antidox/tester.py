import requests
import argparse
import json
import sys
import urllib.parse
import time
from antidox import clean
import datetime
from antidox import perspective
import pywikibot
import os

def wiki_write(result, header):
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
  while True:
    start = datetime.datetime.now() - datetime.timedelta(minutes=2)
    rcstart = start.isoformat()
    page = (args.mediawiki + "api.php?action=query&list=recentchanges&rclimit=500&rcprop=title%7Cids%7Csizes%7Cflags%7Cuser&rcdir=newer&rcstart="+ rcstart + "&rcend=now&format=json")
    get_page = requests.get(page)
    response = json.loads(get_page.content)

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
      print(text)
      #wiki_write(result, header)

      apikey_data, toxicity, dlp = perspective.get_client()
      dlp_response = perspective.dlp_request(dlp, apikey_data, text)
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


        # result = (
        # u'{'
        # +'comment_text:' + str(text) +
        # ', ' + 'contains_pii:' + 'True' + ', ' + 'pii_type:' + str(pii_type) +
        # ', '
        # '}'
        # '\n')
        #wiki_write(result, header)


      if perspective.contains_toxicity(perspective_response):
        header = '==Possibly Toxic Detected: Waiting for review=='
        result = (json.dumps({u"comment_text":text, "contains_toxicity": True,
                               "summaryScore":perspective_response['attributeScores']
                                              ['TOXICITY']['summaryScore']['value']})+"\n")

        # result = (
        #     u'{'
        #     'comment_text:' + str(text) +
        #     ', ' + 'contains_toxicity:' + 'True' + ', ' + 'toxic_score:' +
        #     str(perspective_response['attributeScores']['TOXICITY']['summaryScore']['value']) +
        #     '}'+'\n')
        #wiki_write(result, header)
      time.sleep(120)


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--mediawiki', help='pathway to fake http://sorenj02.nyc.corp.google.com/mediawiki/')
  parser.add_argument('--wikipedia', help='pathway to wikipedia:https://en.wikipedia.org/w ')
  args = parser.parse_args()
  log_change()
