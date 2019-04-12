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
uses K zones, then [0,1] is divided to [x/K, x+1/K) for x varying from 0 to K-1.
so that the comments are scored from all three zones.

The BigQuery table queried to create this sample contains 240M rows (294Gb)
and we assume that 'toxicity', 'cleaned_content', 'replyTo_id' and 'type'
attributes exist. Column 'r' is used to store a random number, used for random sampling,
while column 'toxic_zone' holds the toxicity zone of the comment (e.g., in 3 zones, 0 points
to [0,0.33), 1 to [0.33, 0.66) and 2 to (0.66, 1), while -1 indicates that it
originates from a random sample).

Run as:
python preselect_wikipedia_comments.py \
--bq_project_name "wikidetox-viz" \
--bq_table_name "wikiconv_v2.en_20180701_external" \
--output_json_path "sample.V2.json" \
--zones_num 10 \
--limit_per_zone 10 \
--randomly_selected_limit 0 \
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from tqdm import tqdm
import pandas as pd
import tensorflow as tf
from google.cloud import bigquery

FLAGS = tf.app.flags.FLAGS
tf.app.flags.DEFINE_integer("zones_num", 10, "Number of zones to be used for sampling. One query is run per zone, so keep this below 100 to avoid billing.")
tf.app.flags.DEFINE_integer("limit_per_zone", 100, "Number of comments per zone. When more than one zones are defined, the sample will contain limit_per_zone*zones_num comments.")
tf.app.flags.DEFINE_integer("randomly_selected_limit", 100, "Number of comments selected at random, not based on toxicity.")
tf.app.flags.DEFINE_string("comment_type", "ADDITION", "The type of comment (one of 'ADDITION', 'DELETION', 'CREATION', 'MODIFICATION').")
tf.app.flags.DEFINE_integer("min_txt_len", 1, "Minimum length for comments of the sample.")
tf.app.flags.DEFINE_integer("max_txt_len", 1000, "Maximum length for comments of the sample.")
tf.app.flags.DEFINE_string("bq_table_name", None, "The name of the Google BigQuery table.")
tf.app.flags.DEFINE_string("bq_project_name", None, "The name of the Google BigQuery project.")
tf.app.flags.DEFINE_string("output_csv_path", None, "Path where the output sample CSV should be written. Either that or JSON should not be empty.")
tf.app.flags.DEFINE_string("output_json_path", None, "Path where the output sample JSON should be written. Either that or CSV should not be empty.")

def connect_to_bq(bq_project_name):
    """
    Connect to Google BigQuery
    :param bq_project_name: project name
    :return:
    """
    client = bigquery.Client(project=bq_project_name)
    return client

def query(low_tox, high_tox, limit, max_txt_len, min_txt_len, type, bq_table_name):
    """
    Google Big Query sampling data of specific types
    :param low_tox: comments should be higher than that
    :param high_tox: comments should be lower or equal than that
    :param limit: fetch some
    :param type: kind of comments (wikipedia specific)
    :param max_txt_len: max length of comment
    :param bq_table_name: the table name in BigQuery
    :return: dataframe with results
    """
    assert low_tox>=0 and high_tox<=1
    query = """
    SELECT *, rand() as r 
        FROM `{bq_table_name}`
        WHERE length(cleaned_content)>{min_txt_len} AND length(cleaned_content)<{max_txt_len} AND replyTo_id!="null" AND type="{typ}" AND toxicity>={low} AND toxicity<{high}
        ORDER BY r
        LIMIT {lim}
    """.format(bq_table_name=bq_table_name, low=low_tox, high=high_tox, lim=limit, typ=type, max_txt_len=max_txt_len, min_txt_len=min_txt_len)
    query_job = client.query(query)
    results = query_job.result()
    return results.to_dataframe()


def sample(bq_table_name, toxic_zones_num, min_txt_len, max_txt_len, type, limit, randomly_selected_limit):
    """
    Create a sample of comments using toxic zones and a random batch.
    :param toxic_zones_num:
    :return: toxic_zones_num samples + one with randomly selected comments
    """
    # Create random sample (initialization)
    table = query(low_tox=0, high_tox=1, min_txt_len=min_txt_len, max_txt_len=max_txt_len, limit=randomly_selected_limit, type=type, bq_table_name=bq_table_name)
    table["toxic_zone"] = [-1] * table.shape[0]
    # Add samples following a toxicity-preselection
    for i in tqdm(range(toxic_zones_num)):
        preselected = query(low_tox=float(i)/toxic_zones_num, high_tox=float(i+1)/toxic_zones_num, min_txt_len=min_txt_len, max_txt_len=max_txt_len, limit=limit, type=type, bq_table_name=bq_table_name)
        preselected["toxic_zone"] = [i] * preselected.shape[0]
        # Stack to initialized/updated table
        table = pd.concat([table, preselected], axis=0)
    # Shuffle
    table = table.sample(frac=1).reset_index(drop=True)
    return table


if __name__ == "__main__":
    assert FLAGS.bq_project_name is not None
    assert (FLAGS.output_json_path is None and FLAGS.output_csv_path is not None) or (FLAGS.output_json_path is not None and FLAGS.output_csv_path is None)
    assert FLAGS.comment_type in {'ADDITION', 'DELETION', 'CREATION', 'MODIFICATION'}
    # connect to bq, sample and save
    client = connect_to_bq(FLAGS.bq_project_name)
    table = sample(bq_table_name=FLAGS.bq_table_name, toxic_zones_num=FLAGS.zones_num, min_txt_len=FLAGS.min_txt_len, max_txt_len=FLAGS.max_txt_len, limit=FLAGS.limit_per_zone, type=FLAGS.comment_type, randomly_selected_limit=FLAGS.randomly_selected_limit)
    if FLAGS.output_csv_path is not None:
        # e.g., "sample.11-toxic-zones.addition.csv"
        table.to_csv(FLAGS.output_csv_path, index=False)
    elif FLAGS.output_json_path is not None:
        # e.g., "sample.11-toxic-zones.addition.json"
        table.to_json(path_or_buf=FLAGS.output_json_path, orient="records", lines=True)
    else:
        print ("Not implemented yet.")