from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from tqdm import tqdm
import pandas as pd
import tensorflow as tf

# Connect to Google's BigQuery
from google.cloud import bigquery
client = bigquery.Client(project="wikidetox-viz")

FLAGS = tf.app.flags.FLAGS
tf.app.flags.DEFINE_integer("zones_num", 10, "Number of zones to be used for sampling.")
tf.app.flags.DEFINE_string("output_sample_path", None, "Path where the output sample CSV should be written.")
tf.app.flags.DEFINE_string("output_short_sample_path", None, "Path where the small (100) output sample CSV should be written.")

def query(low_tox=0, high_tox=1, rand=.5, limit=1000, type="ADDITION", max_txt=1000):
    """
    Google Big Query sampling data of specific types
    :param low_tox: comments should be higher than that
    :param high_tox: comments should be lower than that
    :param rand: random selection (p=50%)
    :param limit: fetch some
    :param type: kind of comments (wikipedia specific)
    :param max_txt: max length of comment
    :return: dataframe with results
    """
    query = """
    SELECT * 
        FROM `wikiconv_v2.en_20180701_external`
        WHERE length(cleaned_content)>1 AND length(cleaned_content)<{max_txt} AND replyTo_id!="null" AND type="{typ}" AND toxicity>{low} AND toxicity<{high} AND RAND()<{ran}
        LIMIT {lim}
    """.format(low=low_tox, high=high_tox, ran=rand, lim=limit, typ=type, max_txt=max_txt)
    query_job = client.query(query)
    results = query_job.result()
    return results.to_dataframe()


def sample(toxic_zones_num=10):
    """
    Create a sample of comments using toxic zones and a random batch.
    :param toxic_zones_num:
    :return: toxic_zones_num samples + one with randomly selected comments
    """
    # Create random sample (initialization)
    table = query()
    table["toxic_zone"] = [-1] * table.shape[0]
    # Add samples following a toxicity-preselection
    for i in tqdm(range(toxic_zones_num)):
        preselected = query(low_tox=i / float(toxic_zones_num), high_tox=(i + 1) / float(toxic_zones_num))
        preselected["toxic_zone"] = [i] * preselected.shape[0]
        # Stack to initialized/updated table
        table = pd.concat([table, preselected], axis=0)
    # Shuffle
    table = table.sample(frac=1).reset_index(drop=True)
    return table


if __name__ == "__main__":
    table = sample(FLAGS.zones_num)
    table.to_csv(FLAGS.output_sample_path, index=False) # e.g., "sample.11-toxic-zones.addition.csv"
    table[:100].to_csv(FLAGS.output_sample_path, index=False) # e.g., table[:100].to_csv(, index=False)

