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

Statistical Significance Testing method, used to compare the superiority of a system against
a baseline (based on https://cs.stanford.edu/people/wmorgan/sigtest.pdf)
and whether the agreement (measured with Krippendorff's alpha) of one task is lower
than another.

run as:

python art.py \
--alpha 1 \
--et_coders "gs://path_to_JSON_files/context_pilots_results/agreement/et_coders.json" \
--et_judgments "gs://path_to_JSON_files/context_pilots_results/agreement/et_judgments.json" \
--ht_coders "gs://path_to_JSON_files/context_pilots_results/agreement/ht_coders.json" \
--ht_judgments "gs://path_to_JSON_files/context_pilots_results/agreement/ht_judgments.json" \

"""

import tensorflow as tf
import numpy as np
import pandas as pd
import json
import krippendorff
from sklearn.metrics import accuracy_score, roc_auc_score

FLAGS = tf.app.flags.FLAGS
tf.app.flags.DEFINE_integer("alpha", 1, "1 for Krippendorff's alpha and 0 for system comparison")
tf.app.flags.DEFINE_integer("repetitions", 1000, "Number of samples to be performed.")
# Krippendorff's alpha mode
tf.app.flags.DEFINE_string("et_coders", None, "JSON file with easier task coders UIDs - required for Krippendorff's alpha")
tf.app.flags.DEFINE_string("et_judgments", None, "JSON file with easier task judgments (1:1 with et coders) - required for Krippendorff's alpha")
tf.app.flags.DEFINE_string("ht_coders", None, "JSON file with harder task coders UIDs - required for Krippendorff's alpha")
tf.app.flags.DEFINE_string("ht_judgments", None, "JSON file with harder task judgments (1:1 with ht coders) - required for Krippendorff's alpha")
# System comparison mode
tf.app.flags.DEFINE_string("gold_labels", None, "JSON file with gold labels - required for systems comparison")
tf.app.flags.DEFINE_string("system_predictions", None, "JSON file with predictions of the system in question - required for systems comparison")
tf.app.flags.DEFINE_string("baseline_predictions", None, "JSON file with predictions of the baseline - required for systems comparison")
tf.app.flags.DEFINE_integer("auc", 1, "ROC AUC evaluation between systems under comparison; alternatively, sklearn.metrics.accuracy is used.\n Use appropriate data format with the selected metric.\nSee https://scikit-learn.org/stable/modules/generated/sklearn.metrics.roc_auc_score.html.")


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
        # todo: make this more efficient
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
    :param gold: ground truth labels
    :param system_predictions: predictions of the system of interest, testing if it outperfoms a baseline
    :param baseline_predictions: predictions of the baseline
    :param repetitions: How many samples to be tested; the more the better
    :param evaluator: a function like auc (operating on predictions that are real numbers)
    :return:

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


def alpha(et_coders, et_judgments, ht_coders, ht_judgments, repetitions=1000):
    """
    Assess whether job1 annotators agree more than job2 annotators, employing
    Krippendorff's alpha to measure agreement and approximate randomization test
    for st. significance.
    See https://cs.stanford.edu/people/wmorgan/sigtest.pdf for more about approx. randomization

    :param et_coders: Easier task coders; each row has the coders IDs for a question - aligned with et_judgments
    :param et_judgments: Easier task judgments; each row has the judgments for a question - done by different coders
    :param ht_coders: Harder task coders; each row has the coders IDs for a question - aligned with ht_judgments
    :param ht_judgments: Harder task judgments; each row has the judgments for a question - done by different coders
    :param repetitions: How many samples to be tested; the more the better
    :return: p-value rejecting that alpha of 1st job is greater than that of the 2nd
    """
    rd1 = build_reliability_data(et_coders, et_judgments)
    a1 = krippendorff.alpha(rd1)
    rd2 = build_reliability_data(ht_coders, ht_judgments)
    a2 = krippendorff.alpha(rd2)
    t_obs = a1 - a2
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
        _et_rd = build_reliability_data(_et_coders, _et_judgments)
        _et_a = krippendorff.alpha(_et_rd)
        _ht_rd = build_reliability_data(_ht_coders, _ht_judgments)
        _ht_a = krippendorff.alpha(_ht_rd)

        outcome.append(sided_test(t=(_et_a-_ht_a), t_obs=t_obs))
    return t_obs, np.mean(outcome)


if __name__ == "__main__":
    # art for Krippendorff's alpha
    if FLAGS.alpha == 1:
        et_coders = json.load(open(FLAGS.et_coders))
        et_judgments = json.load(open(FLAGS.et_judgments))
        ht_coders = json.load(open(FLAGS.ht_coders))
        ht_judgments = json.load(open(FLAGS.ht_judgments))
        et_rd = build_reliability_data(et_coders, et_judgments)
        ht_rd = build_reliability_data(ht_coders, ht_judgments)
        print (krippendorff.alpha(et_rd), "VS", krippendorff.alpha(ht_rd))
        a = alpha(et_coders=et_coders,
                  et_judgments=et_judgments,
                  ht_coders=ht_coders,
                  ht_judgments=ht_judgments,
                  repetitions=FLAGS.repetitions)
        print(a)
    # art for system comparison
    else:
        # todo: compile JSON files to test this case
        gold = pd.read_json(FLAGS.gold_labels, orient="records", lines=True)
        system_predictions = pd.read_json(FLAGS.system_predictions, orient="records", lines=True)
        baseline_predictions = pd.read_json(FLAGS.baseline_predictions, orient="records", lines=True)
        # todo: add assertions for labels being in the right format
        if FLAGS.accuracy == 1:
            metric = accuracy_score
        else:
            metric = roc_auc_score
        compare_systems(gold, system_predictions, baseline_predictions, FLAGS.repetitions, metric)