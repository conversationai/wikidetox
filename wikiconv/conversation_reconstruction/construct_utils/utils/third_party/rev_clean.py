# -*- coding: utf-8 -*-
"""Revision cleaning utilties.

Copyright 2017 Google Inc.

Licensed under the Apache License, Version 2.0 (the "License"); you may not
use this file except in compliance with the License.

You may obtain a copy of the License at
http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

-------------------------------------------------------------------------------
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re

import bs4


months = [
    'January',
    'February',
    'March',
    'April',
    'May',
    'June',
    'July',
    'August',
    'September',
    'October',
    'November',
    'December',
    'Jan',
    'Feb',
    'Mar',
    'Apr',
    'May',
    'Jun',
    'Jul',
    'Aug',
    'SJep',
    'Oct',
    'Nov',
    'Dec',
]

month_or = '|'.join(months)
date_p = re.compile(r'\d\d:\d\d,( \d?\d)? (%s)( \d?\d)?,? \d\d\d\d (\(UTC\))?' %
                    month_or)
pre_sub_patterns = [(r'\[\[Image:.*?\]\]', ''), (r'\[\[File:.*?\]\]', ''),
                    (r'\[\[User:.*?\]\]', ''), (r'\[\[user:.*?\]\]', ''),
                    (r'\(?\[\[User talk:.*?\]\]\)?', ''),
                    (r'\(?\[\[user talk:.*?\]\]\)?', ''),
                    (r'\(?\[\[User Talk:.*?\]\]\)?', ''),
                    (r'\(?\[\[User_talk:.*?\]\]\)?', ''),
                    (r'\(?\[\[user_talk:.*?\]\]\)?', ''),
                    (r'\(?\[\[User_Talk:.*?\]\]\)?', ''),
                    (r'\(?\[\[Special:Contributions.*?\]\]\)?', '')]

post_sub_patterns = [('--', ''), (' :', ' '),
                     ('—Preceding .* comment added by   •', '')]


def clean_html(rev):
  """Clean revision HTML."""
  # Remove timestmp.
  ret = re.sub(date_p, lambda x: '', rev)

  # Strip HTML format.
  try:
    ret = bs4.BeautifulSoup(ret, 'html.parser').get_text()
  except:  # pylint: disable=bare-except
    pass
  # Change format for better diff
  ret = re.sub('[\n]+', '\n', str(ret))
  ret = '\n'.join(
      [x.strip() for x in ret.splitlines() if x.strip()]) + '\n'
  if ret == '\n':
    return ''
  return ret


def clean(rev):
  ret = str(rev)
  for p, r in pre_sub_patterns:
    ret = re.sub(p, r, ret)
  # Strip media wiki format.
  for p, r in post_sub_patterns:
    ret = re.sub(p, r, ret)
  return ret
