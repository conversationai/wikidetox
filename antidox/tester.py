import requests
import json
import urllib.request
import time
import clean
import datetime


def wiki_write(result, header):
    site = pywikibot.Site()
    repo = site.data_repository()
    page = pywikibot.Page(site, u"User_talk:" + args.wikibot)

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
    #print (rcstart)

    end = datetime.datetime.now()
    rcend = end.isoformat()
    #print (rcend)
    #rcstart = "now"
    page = ("http://sorenj02.nyc.corp.google.com/mediawiki/api.php?action=query&list=recentchanges&rcstart="+ rcstart + "&rcend=" + rcend + "&rcprop=title%7Cids%7Csizes%7Cflags%7Cuser&rclimit=3&format=json")
    print (page)
    get_page = requests.get(page)
    response = json.loads(get_page.content)

    for change in response['query']['recentchanges']:
      print('new change:')
      revid = str(change['revid'])
      old_revid = str(change['old_revid'])
      compare = ("http://sorenj02.nyc.corp.google.com/mediawiki/api.php?action=compare&fromrev="
              + old_revid + "&torev=" + revid + "&format=json")
      get_compare = requests.get(compare)
      response = json.loads(get_compare.content.decode('utf-8'))

      if 'compare' not in response:
        continue
      revision = response['compare']['*']
      text = clean.content_clean(revision)
      print(text)
      #wiki_write(result, header)
    time.sleep(120)
log_change()
#page = ("http://sorenj02.nyc.corp.google.com/mediawiki/api.php?action=query&list=recentchanges&rcprop=title%7Cids%7Csizes%7Cflags%7Cuser&rclimit=3&format=json")

# start = datetime.datetime.now() - datetime.timedelta(minutes=2)
# rcstart = start.isoformat()
# print (rcstart)

# end = datetime.datetime.now()
# rcend = end.isoformat()
# print (rcend)
# rcstart = "now"
# page = ("http://sorenj02.nyc.corp.google.com/mediawiki/api.php?action=query&list=recentchanges&rcstart="+ rcstart + "&rcend=" + rcend + "&rcprop=title%7Cids%7Csizes%7Cflags%7Cuser&rclimit=3&format=json")
# get_page = requests.get(page)
# response = json.loads(get_page.content)
# print(response['query']['recentchanges'])