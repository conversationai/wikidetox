# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import (
         bytes, dict, int, list, object, range, str,
         ascii, chr, hex, input, next, oct, open,
         pow, round, super,
         filter, map, zip)

from mwtypes import Timestamp
from bs4 import BeautifulSoup
import mwparserfromhell
import re
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
    
def remove_date(comment):
    return re.sub(date_p , lambda x: "", comment)

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

def substitute_patterns(s, sub_patterns):
    for p, r in sub_patterns:
        s = re.sub(p, r, str(s))
    return s

def strip_html(s):
    try:
        s = BeautifulSoup(s, 'html.parser').get_text()
    except:
        pass
    return s

def strip_mw(s):
    parsed = mwparserfromhell.parse(s).strip_code()
    return parsed

def clean(rev):
    ret = remove_date(rev)
    ret = substitute_patterns(ret, pre_sub_patterns)
    ret = strip_mw(ret)
    ret = strip_html(ret)
    ret = substitute_patterns(ret, post_sub_patterns)
    ret = re.sub('[\n]+', '\n', str(ret))
    ret = '\n'.join([x.strip() for x in ret.splitlines() if not(x.strip() == "")])
    return ret
