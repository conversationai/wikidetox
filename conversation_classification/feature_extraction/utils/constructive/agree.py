# Author: Vlad Niculae <vlad@vene.ro>
# License: Simplified BSD

import re

yes_variants = [
    "yes",
    "yea",
    "yep",
    "yup",
    "yeah",
    "ya",
    "ok"]

agree = yes_variants + [
    "i agree",
    "i concur"
    "you're right",
    "you are right",
    "you're probably right",
    "you are probably right",
    "sounds right",
    "looks right",
    "sounds correct",
    "looks correct",
    "sounds accurate",
    "looks accurate",
    "looks good",
    "sounds good",
    "all good",
    "good guess",
    "good to me",
    "absolutely",
    "exactly",
    "you have a point",
    "you've got a point"
]

disagree = [
    "i disagree",
    "i don't agree",
    "i do not agree",
    "that can't be", "that cannot be",
    "i don't think so",
    "are you sure",
    "are we sure"
]

disagree += ["{} {}".format(a, b)
     for a in ["you are", "you're", "that's", "that is", "that sounds"]
     for b in ["wrong", "incorrect", "false"]]

disagree += ["{} but".format(w) for w in yes_variants]

agree_re = re.compile(r"\b({})\b".format("|".join(agree)))
disagree_re = re.compile(r"\b({})\b".format("|".join(disagree)))


def has_disagreement(msgs):
    for msg in msgs:
        msg = msg.lower()
        if disagree_re.findall(msg):
            return True
    return False


def has_agreement(msgs):
    for msg in msgs:
        msg = msg.lower()
        if (msg.startswith("sure ") or
                msg.startswith("true ")) and "?" not in msg:
            return True
        if agree_re.findall(msg):
            return True
    return False
