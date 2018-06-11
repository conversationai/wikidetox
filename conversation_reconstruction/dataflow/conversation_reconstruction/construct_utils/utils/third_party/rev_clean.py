# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import (
         bytes, dict, int, list, object, range, str,
         ascii, chr, hex, input, next, oct, open,
         pow, round, super,
         filter, map, zip)

from bs4 import BeautifulSoup
import re
import resource
import logging
import copy
import time

months = ['January',
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
date_p = re.compile('\d\d:\d\d,( \d?\d)? (%s)( \d?\d)?,? \d\d\d\d (\(UTC\))?' % month_or)
pre_sub_patterns = [
                    ('\[\[Image:.*?\]\]', ""), 
                    ('<!-- {{blocked}} -->', "[BLOCKING_ACTION]"), 
                    ('\[\[File:.*?\]\]', ""), 
                    ('\[\[User:.*?\]\]', ""), 
                    ('\[\[user:.*?\]\]', ""), 
                    ('\(?\[\[User talk:.*?\]\]\)?', ""), 
                    ('\(?\[\[user talk:.*?\]\]\)?', ""), 
                    ('\(?\[\[User Talk:.*?\]\]\)?', ""), 
                    ('\(?\[\[User_talk:.*?\]\]\)?', ""), 
                    ('\(?\[\[user_talk:.*?\]\]\)?', ""), 
                    ('\(?\[\[User_Talk:.*?\]\]\)?', ""),
                    ('\(?\[\[Special:Contributions.*?\]\]\)?', "") 
                   ]


post_sub_patterns = [
                    ('--', ''),
                    (' :', ' '),
		    ('—Preceding .* comment added by   •', "")
                    ]

def clean_html(rev):
    ret = rev
    # Strip HTML format.
    try:
        ret = beautifulsoup(ret, 'html.parser').get_text()
    except:
        pass
    # Change format for better diff
    ret = '\n'.join([x.strip() for x in ret.splitlines() if not(x.strip() == "")]) + '\n'
    if ret == '\n': return ""
    return ret

def clean(rev):
    ret = rev
    # Remove timestmp.
    ret = re.sub(date_p , lambda x: "", rev)
    for p, r in pre_sub_patterns:
        ret = re.sub(p, r, str(ret))
    # Strip media wiki format.
    for p, r in post_sub_patterns:
        ret = re.sub(p, r, str(ret))
    ret = re.sub('[\n]+', '\n', str(ret))
    return ret
