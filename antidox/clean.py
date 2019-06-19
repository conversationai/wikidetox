# -*- coding: utf-8 -*-
r"""HTML cleaning utilties.

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

from bs4 import BeautifulSoup
import mwparserfromhell


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


def remove_date(comment):
  return re.sub(date_p, lambda x: '', comment)


pre_sub_patterns = [(r'\[\[Image:.*?\]\]', ''),
                    (r'<!-- {{blocked}} -->', '[BLOCKING_ACTION]'),
                    (r'\[\[File:.*?\]\]', ''), (r'\[\[User:.*?\]\]', ''),
                    (r'\[\[user:.*?\]\]', ''),
                    (r'\(?\[\[User talk:.*?\]\]\)?', ''),
                    (r'\(?\[\[user talk:.*?\]\]\)?', ''),
                    (r'\(?\[\[User Talk:.*?\]\]\)?', ''),
                    (r'\(?\[\[User_talk:.*?\]\]\)?', ''),
                    (r'\(?\[\[user_talk:.*?\]\]\)?', ''),
                    (r'\(?\[\[User_Talk:.*?\]\]\)?', ''),
                    (r'\(?\[\[Special:Contributions.*?\]\]\)?', '')]

post_sub_patterns = [(r'--', ''), (' :', ' '),
                     (r'—Preceding .* comment added by   \u2022', '')]


def substitute_patterns(s, sub_patterns):
  for p, r in sub_patterns:
    s = re.sub(p, r, s, flags=re.UNICODE)
  return s


def strip_html(s):
  try:
    s = BeautifulSoup(s, 'html.parser').get_text()
  except:  # pylint: disable=bare-except
    pass
  return s


def strip_mw(s):
  try:
    parsed = mwparserfromhell.parse(s, skip_style_tags=True).strip_code()
  except:  # pylint: disable=bare-except
    return s
  return parsed


def content_clean(rev):
  ret = remove_date(rev)
  ret = substitute_patterns(ret, pre_sub_patterns)
  ret = strip_mw(ret)
  ret = strip_html(ret)
  ret = substitute_patterns(ret, post_sub_patterns)
  return ret
