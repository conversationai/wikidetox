"""Constructiveness analysis on StreetCrowd: message-level features.

This is a reimplementation of the features from our paper,

Conversational markers of constructive discussions. Vlad Niculae and
Cristian Danescu-Niculescu-Mizil. In: Proc. of NAACL 2016.
https://vene.ro/constructive/

See the `test` function for a usage example.
"""

# Author: Vlad Niculae <vlad@vene.ro>
# License: Simplified BSD

import re
import os
from collections import defaultdict

from stopwords import stopwords as mallet_stopwords


class Lexicon(object):
    """Word matching code for lexicons.

    Since lexicons may contain multi-word phrases ("I agree") and lexicons may
    overlap, we don't tokenize, use string matching instead.
    """
    def __init__(self, wordlists):
        self.wordlists = wordlists
        self.regex = {cat: self.wordlist_to_re(wordlist)
                      for cat, wordlist in wordlists.items()}

    def wordlist_to_re(self, wordlist):
        return re.compile(r'\b(?:{})\b'.format("|".join(wordlist).lower()))

    def count_words(self, text, return_match=False):
        """Returns a dict {category_name: sum 1[w in category]}

        Words are double-counted if they occur in more
        than one lexicon.
        """
        text_ = text.lower()
        match = {cat: reg.findall(text_) for cat, reg in self.regex.items()}
        count = {cat: len(m) for cat, m in match.items()}

        if return_match:
            return count, match
        else:
            return count

lexicons = {
    'pron_me': ['i', "i'd", "i'll", "i'm", "i've", 'id', 'im', 'ive',
                'me', 'mine', 'my', 'myself'],
    'pron_we': ["let's", 'lets', 'our', 'ours', 'ourselves', 'us',
                'we', "we'd", "we'll", "we're", "we've", 'weve'],
    'pron_you': ["y'all", 'yall', 'you', "you'd", "you'll", "you're",
                 "you've", 'youd', 'youll', 'your', 'youre', 'yours',
                 'youve'],
    'pron_3rd': ['he', "he'd", "he's", 'hed', 'her', 'hers', 'herself',
                 'hes', 'him', 'himself', 'his', 'she', "she'd",
                 "she'll", "she's", 'shes', 'their', 'them', 'themselves',
                 'they', "they'd", "they'll", "they've", 'theyd', 'theyll',
                 'theyve', "they're", "theyre"]
}

with open(os.path.join('lexicons', 'my_geo.txt')) as f:
    lexicons['geo'] = [line.strip().lower() for line in f]

with open(os.path.join('lexicons', 'my_meta.txt')) as f:
    lexicons['meta'] = [line.strip().lower() for line in f]

with open(os.path.join('lexicons', 'my_certain.txt')) as f:
    lexicons['certain'] = [line.strip().lower() for line in f]

with open(os.path.join('lexicons', 'my_hedges.txt')) as f:
    lexicons['hedge'] = [line.strip().lower() for line in f]


lex_matcher = Lexicon(lexicons)


def get_content_tagged(words, tags):
    """Return content words based on tag"""
    return [w for w, tag in zip(words.lower().split(), tags.split())
            if tag in ("N", "^", "S", "Z", "A", "T", "V")]


def message_features(chat, reasons=None, stopwords=mallet_stopwords):
    """Compute message-level features from a chat.

    Parameters
    ----------
    chat, iterable:
        sequence of tuples (user, tokens, tags, timestamp) where
        tokens and tags are whitespace-separated strings.

    reasons, iterable:
        sequence of tuples (user, tokens, tags).
        In StreetCrowd, users individually can leave an explanation for their
        solo game decision.  These reasons populate the chat when the team
        meets, but they have no intrinsic order, so they can only introduce
        but not adopt idea words.  Also, more than one reason can introduce
        an idea, because they are written independently.

    """
    seen_words = set()
    introduced = defaultdict(set)
    where_introduced = defaultdict(list)
    repeated = defaultdict(set)

    reason_features = []
    msg_features = []

    for k, (user, tokens, tags) in enumerate(reasons):
        features = {}
        content_words = [w for w in get_content_tagged(tokens, tags)
                         if w not in stopwords]

        # all new content words are new ideas here
        introduced[user].update(content_words)
        seen_words.update(content_words)
        for w in content_words:
            where_introduced[w].append(('reason', k))

        # length statistics
        features['n_words'] = len(tokens.split())
        lex_counts = lex_matcher.count_words(tokens)
        features.update(lex_counts)

        # fillers
        features['n_introduced'] = 0
        features['n_introduced_w_certain'] = 0
        features['n_introduced_w_hedge'] = 0
        reason_features.append(features)

    for k, (user, tokens, tags, timestamp) in enumerate(chat):
        features = dict()

        # length statistics
        features['n_words'] = len(tokens.split())

        # count lexicon words
        lex_counts = lex_matcher.count_words(tokens)
        features.update(lex_counts)

        # ideas introduced (provisory; ideas only count if they're adopted)
        content_words = [w for w in get_content_tagged(tokens, tags) if
                         w not in stopwords]
        new_words = [w for w in content_words if w not in seen_words]
        introduced[user].update(new_words)

        for w in new_words:
            where_introduced[w].append(('message', k))

        n_adopted = 0
        for user_b, introduced_b in introduced.items():
            if user_b == user:
                continue

            repeated_words = [w for w in content_words if w in introduced_b]
            n_adopted += len(repeated_words)
            repeated[user, user_b].update(repeated_words)

        features['n_adopted'] = n_adopted
        features['n_adopted_w_hedge'] = n_adopted * features['hedge']
        features['n_adopted_w_certain'] = n_adopted * features['certain']

        seen_words.update(new_words)

        features['n_introduced'] = 0
        features['n_introduced_w_certain'] = 0
        features['n_introduced_w_hedge'] = 0
        msg_features.append(features)

    # second pass to fix idea introduction features
    for repeated_words in repeated.values():
        for w in repeated_words:
            for src_type, ix in where_introduced[w]:
                src = reason_features if src_type == 'reason' else msg_features
                src[ix]['n_introduced'] += 1
                src[ix]['n_introduced_w_hedge'] += src[ix]['hedge']
                src[ix]['n_introduced_w_certain'] += src[ix]['certain']
    return msg_features, reason_features


def test():

    # Sample run on toy data slightly adapted from the real dataset.
    # reasons: (username, tokens, pos_tags)
    test_reasons = [(
            'User00511',
            'saw a sign that said " YIELD right of way " so uk somewhere ?',
            'V D N P V , V R P N , R R R ,'
        ),
        (
            'User00510',
            '',
            ''
        ),
        (
            'User00510',
            ('Uses *** *** *** . Has sheep . Very *** house . Green and *** '
             'looking'),
            'V * * * , V N , R * N , A & * V'
        )
    ]

    # chats: (username, tokens, pos_tags, timestamp)
    test_chat = [[
            "User00510",
            "bunch of *** *** ***",
            "N P * * *",
            1447121991.0
        ],
        [
            "User00510",
            "could be anywhere . am ***",
            "V V R , V *",
            1447121998.0
        ],
        [
            "User00510",
            ("no way *** *** are that *** . must be asia . no monkey gonna "
             "be *** next to people in north america . *** would see a *** "
             "and just *** the thing . the *** would just say sorry to it and "
             "let it run the country"),
            ("D N * * V D * , V V ^ , D N V V * R P N P ^ ^ , * V V D * & R * "
             "D N , D * V R V A P O & V O V D N"),
            1447122063.0
        ],
        [
            "User00184",
            "japanese writing on the building",
            "^ V P D N",
            1447122115.0
        ],
        [
            "User00184",
            "this is a famous sheep",
            "O V D A N",
            1447122116.0
        ],
        [
            "User00510",
            "yes maybe they think those are building",
            "! R O V O V N",
            1447122149.0
        ]
    ]

    msg_feat, reason_feat =  message_features(test_chat, test_reasons)

    for row in reason_feat + msg_feat:
        print(row)


if __name__ == '__main__':
    test()

