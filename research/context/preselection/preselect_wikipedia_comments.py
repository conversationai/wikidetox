# coding=utf-8
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
"""Preselect Wikipedia comments.

A library to preselect wikipedia comments based on their toxicity score
among others aspects.

The initial goal was to create a sample of comments to use for annotation;
the sample was stratified to ensure existence of toxic comments. If one
uses 3 zones, then [0,1] will be divided in [0,0.33), [0.33,0.66) and
[0.66,1], so that the comments are scored from all three zones.

The BigQuery table queried to create this sample contains 240M rows (332Gb).

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from tqdm import tqdm
import pandas as pd
import tensorflow as tf
from google.cloud import bigquery

FLAGS = tf.app.flags.FLAGS
tf.app.flags.DEFINE_integer("limit", 100, "Number of comments per zone (zones_num*limit + 1).")
tf.app.flags.DEFINE_integer("randomly_selected_limit", 100, "Number of comments selected at random, not based on toxicity.")
tf.app.flags.DEFINE_string("comment_type", "ADDITION", "The type of comment ('ADDITION', 'DELETION', 'CREATION', 'MODIFICATION').")
tf.app.flags.DEFINE_integer("max_txt_len", 1000, "Maximum length for comments of the sample.")
tf.app.flags.DEFINE_string("bgq_project_name", None, "The name of the Google BigQuery project.")
tf.app.flags.DEFINE_integer("zones_num", 10, "Number of zones to be used for sampling.")
tf.app.flags.DEFINE_string("output_csv_path", None, "Path where the output sample CSV should be written.")
tf.app.flags.DEFINE_string("output_json_path", None, "Path where the output sample JSON should be written.")

def connect_to_gbq(gbq_project_name):
    """
    Connect to Google BigQuery
    :param gbq_project_name: project name
    :return:
    """
    client = bigquery.Client(project=gbq_project_name)
    return client

def query(low_tox, high_tox, limit, max_txt_len, type):
    """
    Google Big Query sampling data of specific types
    :param low_tox: comments should be higher than that
    :param high_tox: comments should be lower than that
    :param limit: fetch some
    :param type: kind of comments (wikipedia specific)
    :param max_txt_len: max length of comment
    :return: dataframe with results
    """
    assert low_tox>=0 and high_tox<=1
    query = """
    SELECT *, rand() as r 
        FROM `wikiconv_v2.en_20180701_external`
        WHERE length(cleaned_content)>1 AND length(cleaned_content)<{max_txt_len} AND replyTo_id!="null" AND type="{typ}" AND toxicity>{low} AND toxicity<{high}
        order by r
        LIMIT {lim}
    """.format(low=low_tox, high=high_tox, lim=limit, typ=type, max_txt_len=max_txt_len)
    query_job = client.query(query)
    results = query_job.result()
    return results.to_dataframe()


def sample(toxic_zones_num, max_txt_len, type, limit, randomly_selected_limit):
    """
    Create a sample of comments using toxic zones and a random batch.
    :param toxic_zones_num:
    :return: toxic_zones_num samples + one with randomly selected comments
    """
    # Create random sample (initialization)
    table = query(low_tox=0, high_tox=1, max_txt_len=max_txt_len, limit=randomly_selected_limit, type=type)
    table["toxic_zone"] = [-1] * table.shape[0]
    # Add samples following a toxicity-preselection
    for i in tqdm(range(toxic_zones_num)):
        preselected = query(low_tox=float(i)/toxic_zones_num, high_tox=float(i+1)/toxic_zones_num, max_txt_len=max_txt_len, limit=limit, type=type)
        preselected["toxic_zone"] = [i] * preselected.shape[0]
        # Stack to initialized/updated table
        table = pd.concat([table, preselected], axis=0)
    # Shuffle
    table = table.sample(frac=1).reset_index(drop=True)
    return table


if __name__ == "__main__":
    assert FLAGS.bgq_project_name is not None
    assert (FLAGS.output_json_path is None and FLAGS.output_csv_path is not None) or (FLAGS.output_json_path is not None and FLAGS.output_csv_path is None)
    assert FLAGS.comment_type in {'ADDITION', 'DELETION', 'CREATION', 'MODIFICATION'}
    # connect to gbq, sample and save
    client = connect_to_gbq(FLAGS.bgq_project_name)
    table = sample(toxic_zones_num=FLAGS.zones_num, max_txt_len=FLAGS.max_txt_len, limit=FLAGS.limit, type=FLAGS.comment_type, randomly_selected_limit=FLAGS.randomly_selected_limit)
    if FLAGS.output_csv_path is not None:
        # e.g., "sample.11-toxic-zones.addition.csv"
        table.to_csv(FLAGS.output_csv_path, index=False)
    elif FLAGS.output_json_path is not None:
        # e.g., "sample.11-toxic-zones.addition.json"
        table.to_json(path_or_buf=FLAGS.output_json_path, orient="records", lines=True)
    else:
        print ("Not implemented yet.")