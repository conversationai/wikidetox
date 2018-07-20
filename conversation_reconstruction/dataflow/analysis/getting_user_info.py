"""
Copyright 2018 Google Inc.
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

-------------------------------------------------------------------------------

A utility function to fetch user data from Wikipedia.

Run with:

  python getting_user_info.py
    --total_user=NumberOfQueries
    --input_file=JSONFileOfUsers
    --output_file=OutputFileForUserInformation
    --start_point=StartFromANonZeroPointInFile

"""

import json
import logging
import requests
import argparse

THERESHOLD = 50
FIELDS = 'blockinfo|groups|editcount|rights|registration|emailable|gender'
SCHEMA = 'user_text|user_id|is_bot|is_admin|is_bureaucrat|blockinfo|editcount|registration|emailable|gender'.split('|')

def get_info(users):
  baseurl = 'http://en.wikipedia.org/w/api.php'
  my_atts = {}
  my_atts['action'] = 'query'
  my_atts['format'] = 'json'
  my_atts['list'] = 'users'
  my_atts['ususers'] = '|'.join(users)
  my_atts['usprop'] = FIELDS

  resp = requests.get(baseurl, params = my_atts)
  if not(resp.status_code == 200):
    # The query to Wikipedia returned an error, writing the errors to a
    # separate output file.
    with open("exceptions.json", "a") as e:
      e.write(json.dumps(users) + '\n')
      e.write(resp.status_code)
    return []
  else:
    data = resp.json()['query']['users']
    ret = []
    for dat in data:
      cur = {}
      for s in SCHEMA: cur[s] = None
      cur.update({"user_text": dat['name']})
      for s in SCHEMA:
        if s in dat:
          cur[s] = dat[s]
      if 'groups' in dat:
       g = dat['groups']
       for group in ['bot', 'admin', 'bureaucrat']:
         field = 'is_%s' % group
         cur[field] = False
         if group in g: cur[field] = True
       if 'admins' in g or 'sysop' in g:
         cur['is_admin'] = True
      if 'userid' in dat:
        cur['user_id'] = dat['userid']
      if cur['gender'] == 'unknown':
        cur['gender'] = None
      ret.append(cur)
    return ret

if __name__ == '__main__':
  logging.getLogger().setLevel(logging.INFO)
  users = []
  progress = 0
  parser = argparse.ArgumentParser()
  parser.add_argument('--total_user',
                      dest='total_user',
                      default='Unknown')
  parser.add_argument('--input_file',
                      dest='input_data',
                      default=None,
                      help='Location of the input data in json format.')
  parser.add_argument('--output_file',
                      dest='output_data',
                      default=None,
                      help='Location of the ouptut data.')
  parser.add_argument('--start_point',
                      dest='start_point',
                      default=0,
                      help='If the code stopped last time, you can resume from the breaking point using this argument.')
  known_args, _ = parser.parse_known_args()
  total = known_args.total_user
  with open(known_args.output_data, "w") as w, open(known_args.input_data, "r") as f:
      for ind, line in enumerate(f):
        # Skipping processed input
        if ind < known_args.start_point:
          continue
        data = json.loads(line)
        user = data['user_text']
        progress += 1
        users.append(user)
        if progress % 5000 == 0:
          logging.info("{progress}/{total} finished.".format(progress=progress, total=total))
        if len(users) == THERESHOLD:
          # Sending 50 queries in a batch to Wikipedia since 50 is the maximum
          # amount.
          info = get_info(users)
          for i in info:
              w.write(json.dumps(i) + '\n')
          users = []
      if len(users) > 0:
        info = get_info(users)
        for i in info:
          w.write(json.dumps(i) + '\n')
