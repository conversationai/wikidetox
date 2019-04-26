# -*- coding: utf-8 -*-
# Copyright 2018 The Conversation-AI.github.io Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
approximate randomization test (art)

This is a st. significance testing method to assess whether the agreement
in an annotation task is st. significantly higher than another one.

It is based on the a.r. test used to compare the superiority of a system against
a baseline (see https://cs.stanford.edu/people/wmorgan/sigtest.pdf).

INFO: The two tasks should contain annotations of the same texts
for the result to be valid.

Run as:

python art.py \
--et_coders "et_coders.json" \
--et_judgments "et_labels.json" \
--ht_coders "ht_coders.json" \
--ht_judgments "ht_labels.json" \
--repetitions 1000 \

# You can also use "gs://path.json" file paths.
"""

import tensorflow as tf
import numpy as np
import json
import krippendorff
from sklearn.metrics import accuracy_score

FLAGS = tf.app.flags.FLAGS
tf.app.flags.DEFINE_integer("repetitions", 1000, "Number of samples to be performed.")
tf.app.flags.DEFINE_string("et_coders", None, "JSON file with easier task coders UIDs - required for Krippendorff's alpha")
tf.app.flags.DEFINE_string("et_judgments", None, "JSON file with easier task judgments (1:1 with et coders) - required for Krippendorff's alpha")
tf.app.flags.DEFINE_string("ht_coders", None, "JSON file with harder task coders UIDs - required for Krippendorff's alpha")
tf.app.flags.DEFINE_string("ht_judgments", None, "JSON file with harder task judgments (1:1 with ht coders) - required for Krippendorff's alpha")

for flag in ["et_coders", "ht_coders", "et_judgments", "ht_judgments"]:
    tf.app.flags.mark_flag_as_required(flag)


def scramble(judgments, columns_only=True):
    """
    scramble an array of judgments (each row is one question)
    :param judgments:
    :param columns_only:
    :return:
    """
    n = judgments.shape[1]
    if columns_only:
        return judgments[:, np.random.permutation(n)]
    else:
        # This can/should be more efficient
        for rec in judgments:
            np.random.shuffle(rec)
        return judgments


def build_reliability_data(coders_list, labels_list):
    """
    Build a reliability data matrix to be used for Krippendorff's alpha calculation
    :param coders_list: a list of lists, each being the coder UIDs for a unit question
    :param labels_list: a list of lists, each being the coder judgments for a unit question (1:1 with coders_list)
    :return: a numpy reliability data matrix (i.e., each row being a coder, each column being a judgment)

    >>> matrix = build_reliability_data([["a", "c", "b"], ["b", "d", "a"]], [[1,0,1],[0,1,1]])

    """
    coders = list({coder for unit_coders in coders_list for coder in unit_coders})
    # index the coders, from 0 to |coders|
    coders2index = lambda coder: coders.index(coder)
    reliability_data = [[] for _ in coders]
    # for each coder create a row and find all judgments
    for coder in coders:
        # for this coder get his/her ID
        cid = coders2index(coder)
        # zip coders and judgments across rows
        for coders_in_unit, labels_in_unit in zip(coders_list, labels_list):
            # if the coder has judged this question find his/her judgment, else put np.nan
            if coder in set(coders_in_unit):
                coder_position_in_unit = coders_in_unit.index(coder)
                label = labels_in_unit[coder_position_in_unit]
            else:
                label = np.nan
            # update the reliability data for that coder (use his/her index)
            reliability_data[cid].append(label)
    return np.array(reliability_data)


def sided_test(t, t_obs):
    """
    Compare the hypothesis, whether t is greater than t_observed. This is one-side test.
    :param t: sample assessment between the two candidates
    :param t_obs: original assessment between the two candidates
    :return: 1 if sample assessment is better else 0
    """
    comparison = t > t_obs
    return int(comparison)


def compare_systems(gold, system_predictions, baseline_predictions, repetitions=1000, evaluator=None):
    """
    Use an approximate randomization test to assess whether a "system" is better than a "baseline".
    (See https://cs.stanford.edu/people/wmorgan/sigtest.pdf for more about approx. randomization)

    :param gold: ground truth labels
    :param system_predictions: predictions of the system of interest, testing if it outperfoms a baseline
    :param baseline_predictions: predictions of the baseline
    :param repetitions: How many samples to be tested; the more the better
    :param evaluator: a function like auc (operating on predictions that are real numbers)
    :return: p value

    An example would be a Gaussian (with mean close to major class) winning a 'uniform' on an imbalanced problem:
    >>> system_predictions = [round(x) for x in np.random.normal(0.8, 0.3, 100)] # normal close to 1
    >>> baseline_predictions = [round(x) for x in np.random.uniform(size=100)] # uniform
    >>> gold = 90*[1] + 10*[0]
    >>> gauss_vs_uniform = compare_systems(gold, system_predictions, baseline_predictions, 1000, accuracy_score)
    >>> gauss_vs_uniform < 0.05
    True
    >>> #or two uniform (random) distributions:
    >>> system_predictions = [round(x) for x in np.random.uniform(size=100)] # normal close to 1
    >>> baseline_predictions = [round(x) for x in np.random.uniform(size=100)] # uniform
    >>> gold = 90*[1] + 10*[0]
    >>> uni_vs_uni = compare_systems(gold, system_predictions, baseline_predictions, 1000, accuracy_score)
    >>> uni_vs_uni > 0.05
    True

    """
    p1 = evaluator(gold, system_predictions)
    p2 = evaluator(gold, baseline_predictions)
    t_obs = p1-p2
    outcome = []
    for _ in range(repetitions):
        _predictions1 = []
        _predictions2 = []
        for i in range(len(system_predictions)):
            if np.random.random()>.5:
                _predictions1.append(system_predictions[i])
                _predictions2.append(baseline_predictions[i])
            else:
                _predictions1.append(baseline_predictions[i])
                _predictions2.append(system_predictions[i])
        # compare the two systems
        p1 = evaluator(gold, _predictions1)
        p2 = evaluator(gold, _predictions2)
        # test h0
        outcome.append(sided_test(t=p1-p2, t_obs=t_obs))
    return np.mean(outcome)


def compare(et_coders, et_judgments, ht_coders, ht_judgments):
    """
    Compare the agreement between two annotation jobs <et> and <ht>.
    :param et_coders: coders of the easier task
    :param et_judgments: labels assigned by the coders of the easier task
    :param ht_coders: coders of the harder task
    :param ht_judgments: labels assigned by the coders of the harder task
    :return: difference between the agreement of <et> and <ht>
    """
    rd1 = build_reliability_data(et_coders, et_judgments)
    a1 = krippendorff.alpha(rd1)
    rd2 = build_reliability_data(ht_coders, ht_judgments)
    a2 = krippendorff.alpha(rd2)
    return a1 - a2


def sample(et_coders, et_judgments, ht_coders, ht_judgments, repetitions=1000):
    """
    Assess the statistical significance of the claim that the Easier Task Coders (et_coders)
    agree more than the Harder Task Coders (ht_coders).

    :param et_coders: Easier task coders; each row has the coders IDs for a question - aligned with et_judgments
    :param et_judgments: Easier task judgments; each row has the judgments for a question - done by different coders
    :param ht_coders: Harder task coders; each row has the coders IDs for a question - aligned with ht_judgments
    :param ht_judgments: Harder task judgments; each row has the judgments for a question - done by different coders
    :param repetitions: How many samples to be tested; the more the better
    :return: p-value rejecting that alpha of 1st job is greater than that of the 2nd
    """
    t_obs = compare(et_coders, et_judgments, ht_coders, ht_judgments)
    outcome = []
    for _ in range(repetitions):
        _et_coders, _et_judgments = [],[]
        _ht_coders, _ht_judgments = [],[]
        for i in range(len(et_judgments)):
            if np.random.random()>.5:
                _et_coders.append(et_coders[i])
                _et_judgments.append(et_judgments[i])
                _ht_coders.append(ht_coders[i])
                _ht_judgments.append(ht_judgments[i])
            else:
                _et_coders.append(ht_coders[i])
                _et_judgments.append(ht_judgments[i])
                _ht_coders.append(et_coders[i])
                _ht_judgments.append(et_judgments[i])
        # compare the two
        t = compare(_et_coders, _et_judgments, _ht_coders, _ht_judgments)
        outcome.append(sided_test(t=t, t_obs=t_obs))
    return t_obs, np.mean(outcome)


def load_json(filepath=None):
    """
    Load a JSON file from Google Storage or a local path.
    :param filepath:
    :return: the JSON file
    """
    assert filepath is not None
    with tf.gfile.Open(filepath, 'r') as o:
        read_file = o.read()
    return json.loads(read_file)


if __name__ == "__main__":
    et_coders = load_json(FLAGS.et_coders)
    et_judgments = load_json(FLAGS.et_judgments)
    ht_coders = load_json(FLAGS.ht_coders)
    ht_judgments = load_json(FLAGS.ht_judgments)
    a = sample(et_coders=et_coders,
               et_judgments=et_judgments,
               ht_coders=ht_coders,
               ht_judgments=ht_judgments,
               repetitions=FLAGS.repetitions)
    print(a)