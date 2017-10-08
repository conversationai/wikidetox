"""Constructiveness analysis on StreetCrowd: turn-level features.

This is a reimplementation of the features from our paper,

Conversational markers of constructive discussions. Vlad Niculae and
Cristian Danescu-Niculescu-Mizil. In: Proc. of NAACL 2016.
http://vene.ro/constructive/

See the `test` function for a usage example.
"""

# Author: Vlad Niculae <vlad@vene.ro>
# License: Simplified BSD

from stopwords import stopwords

from agree import has_agreement, has_disagreement


def sublist_bigrams(pos_list):
    """ bigrams at sublist level
    >>> sublist_bigrams(['V V', 'R , V O V D N', 'P O V'])
    [('V', 'V'), ('R', ','), (',', 'V'), ('V', 'O'), ('P', 'O'), ('O', 'V')]
    """
    pos_list = [s.split() for s in pos_list]

    bigrams = [
        (a, b)
        for poss in pos_list
        for a, b in zip(poss, poss[1:])
    ]

    return bigrams


def turns_from_chat(chat):
    if len(chat) == 0:
        return []
    prev_user, prev_words, prev_pos, prev_time = chat[0]
    prev_words = [prev_words]
    prev_pos = [prev_pos]

    gap = None

    turns = []
    for user, words, pos, time in chat[1:]:
        if user == prev_user:
            prev_words.append(words)
            prev_pos.append(pos)
            prev_time = time
        else:
            turns.append((gap, prev_user, prev_words, prev_pos))
            prev_user = user
            prev_words = [words]
            prev_pos = [pos]
            gap = time - prev_time
    turns.append((gap, prev_user, prev_words, prev_pos))
    return turns


def turn_features(turns):
    """Turn-based features.

    Parameters
    ----------
    turns: iterable,
        Sequence of (gap, prev_user, prev_tokens, prev_pos) as returned by
        the turns_from_chat function.
    """

    turn_features = []

    for prev_turn, curr_turn in zip(turns, turns[1:]):
        features = {}

        _, prev_user, prev_words, prev_pos = prev_turn
        gap, user, words, pos = curr_turn

        if has_agreement(words):
            features['agree'] = 1
        if has_disagreement(words):
            features['disagree'] = 1

        # words and accommodation
        words = [w.lower() for msg in words for w in msg.split()]
        prev_words = [w.lower() for msg in prev_words for w in msg.split()]

        prev_stop = set([w for w in prev_words if w in stopwords])
        prev_content = [w for w in prev_words if w not in stopwords]

        prev_content = set(prev_content)

        stop_repeat = [w for w in words if w in prev_stop]
        content_repeat = [w for w in words if w in prev_content]

        if len(content_repeat):
            features['n_repeated_content'] = len(content_repeat)

        if len(stop_repeat):
            features['n_repeated_stop'] = len(stop_repeat)

        # part-of-speech bigram accommodation
        pos_bigrams = sublist_bigrams(pos)
        prev_pos_bigrams = set(sublist_bigrams(prev_pos))

        pos_repeat = [p for p in pos_bigrams if p in prev_pos_bigrams]

        features['n_repeated_pos_bigram'] = len(pos_repeat)
        features['gap'] = gap
        turn_features.append(features)

    return turn_features


def test():
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

    for turn in turn_features(turns_from_chat(test_chat)):
        print(turn)

if __name__ == '__main__':
    test()
