#
# A basic bag of words classifier for the Toxic Comment Classification Kaggle
# challenge (https://www.kaggle.com/c/jigsaw-toxic-comment-classification-challenge).
#
# TODO:
#  * flag for y_class
#  * fix batching
#  * write way to view predictions
#  * write out test predictions
#  * hook up tensorboard
#  * print probabilities of predictions

import argparse
import sys

import pandas as pd
import tensorflow as tf
import numpy as np
from sklearn import metrics

FLAGS = None

MAX_DOCUMENT_LENGTH = 1000 # TODO: should probably check that this is right
MAX_LABEL = 2
Y_CLASSES = ['toxic', 'severe_toxic','obscene','threat','insult','identity_hate']

TRAIN_PERCENT = .8 # Percent of data to allocate to training
DATA_SEED = 48173 # Random seed used for splitting the data into train/test
EMBEDDING_SIZE = 50
WORDS_FEATURE = 'words'  # Name of the input words feature.

TRAIN_SEED = 9812  # Random seed used to initialize training
TRAIN_STEPS = 100 # Number of steps to take while training
LEARNING_RATE = 0.01
BATCH_SIZE = 5000

PREDICT_WRITE_PATH = 'predicted.csv' # place to write csv of predictions
class WikiData:

  def __init__(self, path):
    self.data = self._load_data(path)
    self.data['comment_text'] = self.data['comment_text'].astype(str)

  def _load_data(self, path):
      df =  pd.read_csv(path)

      return df

  def split(self, train_percent, y_class, seed):
    """
    Split divides the Wikipedia data into test and train subsets.

    Args:
      * train_percent (float): the fraction of data to use for training
      * y_class (string): the attribute of the wiki data to predict, e.g. 'toxic'
      * seed (integer): a seed to use to split the data in a reproducible way

    Returns:
      x_train (dataframe): the comment_text for the training data
      y_train (dataframe): the 0 or 1 labels for the training data
      x_test (dataframe): the comment_text for the test data
      y_test (dataframe): the 0 or 1 labels for the test data
    """

    if y_class not in Y_CLASSES:
      tf.logging.error('Specified y_class {0} not in list of possible classes {1}'\
            .format(y_class, Y_CLASSES))
      raise ValueError

    if train_percent >= 1 or train_percent <= 0:
      tf.logging.error('Specified train_percent {0} is not between 0 and 1'\
            .format(train_percent))
      raise ValueError

    # Sample the data to create training data
    data_train = self.data.sample(frac=train_percent, random_state=seed)

    # Use remaining examples as test data
    data_test = self.data[self.data["id"].isin(data_train["id"]) == False]

    x_train = data_train['comment_text']
    x_test = data_test['comment_text']
    y_train = data_train[y_class]
    y_test = data_test[y_class]

    return x_train, x_test, y_train, y_test

def estimator_spec_for_softmax_classification(logits, labels, mode):
  """
  Depending on the value of mode, different EstimatorSpec arguments are required.

  For mode == ModeKeys.TRAIN: required fields are loss and train_op.
  For mode == ModeKeys.EVAL: required field is loss.
  For mode == ModeKeys.PREDICT: required fields are predictions.

  Returns EstimatorSpec instance for softmax classification.
  """
  predicted_classes = tf.argmax(logits, axis=1)
  predictions = {
    'classes': predicted_classes,

    # Add softmax_tensor to the graph. It is used for PREDICT and for training
    # logging
    'probabilities': tf.nn.softmax(logits, name='softmax_tensor')
  }

  # PREDICT Mode
  if mode == tf.estimator.ModeKeys.PREDICT:
    return tf.estimator.EstimatorSpec(mode=mode, predictions=predictions)

  # Calculate Loss (for both TRAIN and EVAL modes)
  #
  # Note: this line with throw an exception in PREDICT mode since all the
  # labels will be NONE.
  loss = tf.losses.sparse_softmax_cross_entropy(labels=labels, logits=logits)

  # TRAIN Mode
  if mode == tf.estimator.ModeKeys.TRAIN:
    optimizer = tf.train.AdamOptimizer(learning_rate=LEARNING_RATE)
    train_op = optimizer.minimize(loss, global_step=tf.train.get_global_step())

    tensors_to_log= {'loss': loss}
    logging_hook = tf.train.LoggingTensorHook(
      tensors=tensors_to_log, every_n_iter=10)

    return tf.estimator.EstimatorSpec(
      mode=mode,
      loss=loss,
      train_op=train_op,
      training_hooks=[logging_hook],
      predictions={'loss': loss}
    )

  # EVAL Mode
  eval_metric_ops = {
    'accuracy': tf.metrics.accuracy(labels=labels, predictions=predicted_classes)
  }

  return tf.estimator.EstimatorSpec(
    mode=mode, loss=loss, eval_metric_ops=eval_metric_ops)

def bag_of_words_model(features, labels, mode):
  """
  A bag-of-words model. Note it disregards the word order in the text.

  Returns a tf.estimator.EstimatorSpec. An EstimatorSpec fully defines the model
  to be run by an Estimator.
  """

  bow_column = tf.feature_column.categorical_column_with_identity(
      WORDS_FEATURE, num_buckets=n_words)

  # The embedding values are initialized randomly, and are trained along with
  # all other model parameters to minimize the training loss.
  bow_embedding_column = tf.feature_column.embedding_column(
      bow_column, dimension=EMBEDDING_SIZE)

  bow = tf.feature_column.input_layer(
      features,
      feature_columns=[bow_embedding_column])

  logits = tf.layers.dense(bow, MAX_LABEL, activation=None)

  return estimator_spec_for_softmax_classification(
      logits=logits, labels=labels, mode=mode)

def main():
    global n_words

    tf.logging.set_verbosity(tf.logging.INFO)

    if FLAGS.verbose:
      tf.logging.info('Running in verbose mode')
      tf.logging.set_verbosity(tf.logging.DEBUG)

    # Load data
    tf.logging.debug('Loading data {}'.format(FLAGS.train_data))
    data = WikiData(FLAGS.train_data)

    # Split data
    x_train_text, x_test_text, y_train, y_test \
      = data.split(TRAIN_PERCENT, 'toxic', DATA_SEED)

    # Process data
    vocab_processor = tf.contrib.learn.preprocessing.VocabularyProcessor(
      MAX_DOCUMENT_LENGTH)

    x_train = np.array(list(vocab_processor.fit_transform(x_train_text)))
    x_test = np.array(list(vocab_processor.fit_transform(x_test_text)))
    y_train = np.array(y_train)
    y_test = np.array(y_test)

    n_words = len(vocab_processor.vocabulary_)
    tf.logging.info('Total words: %d' % n_words)

    # Build model

    # Note: model_fn is of type tf.estimator.EstimatorSpec
    model_fn = bag_of_words_model

    # Subtract 1 because VocabularyProcessor outputs a word-id matrix where word
    # ids start from 1 and 0 means 'no word'. But categorical_column_with_identity
    # assumes 0-based count and uses -1 for missing word.
    x_train -= 1
    x_test -= 1

    classifier = tf.estimator.Estimator(
      model_fn=model_fn,
      config=tf.contrib.learn.RunConfig(
        tf_random_seed=TRAIN_SEED,
      ),
      model_dir="/tmp/kaggle_model")

    # Train
    train_input_fn = tf.estimator.inputs.numpy_input_fn(
      x={WORDS_FEATURE: x_train},
      y=y_train,
      batch_size=BATCH_SIZE,
      num_epochs=None,
      shuffle=True)

    classifier.train(
      input_fn=train_input_fn,
      steps=TRAIN_STEPS)

    # Predict on held-out data
    test_input_fn = tf.estimator.inputs.numpy_input_fn(
      x={WORDS_FEATURE: x_test},
      y=y_test,
      num_epochs=1,
      shuffle=False)

    # TODO: figure out why we can only read predictions once
    test_predictions = classifier.predict(input_fn=test_input_fn)
    y_test_predicted = np.array(list(p['classes'] for p in test_predictions))

    data_test = x_train_text
    data_test[FLAGS.y_class] = y_test
    data_test[FLAGS.y_class + '_predicted'] = y_test_predicted

    tf.logging.info("Writing held-out test predictions to {}"
                    .format(TEST_WRITE_PATH))
    data_predict.to_csv(TEST_WRITE_PATH)

    # Score with sklearn
    sklearn_score = metrics.accuracy_score(y_test, y_test_predicted)

    # Score with TensorFlow
    tf_scores = classifier.evaluate(input_fn=test_input_fn)

    tf.logging.info('')
    tf.logging.info('Accuracy (sklearn)\t: {0:f}'.format(sklearn_score))
    tf.logging.info('Accuracy (tensorflow)\t: {0:f}'.format(tf_scores['accuracy']))

    # Predict on prediction data (no labels)
    tf.logging.info('')
    tf.logging.info('Generating predictions for {}'.format(FLAGS.predict_data))

    data_predict = WikiData(FLAGS.predict_data).data
    x_predict = np.array(list(
      vocab_processor.fit_transform(data_predict['comment_text'])))

    predict_input_fn = tf.estimator.inputs.numpy_input_fn(
      x={WORDS_FEATURE: x_predict},
      num_epochs=1,
      shuffle=False)

    predict_predictions = classifier.predict(input_fn=predict_input_fn)
    y_predicted = np.array(list(p['classes'] for p in predict_predictions))

    data_predict['y_predicted'] = y_predicted
    tf.logging.info("Writing predictions to {}".format(PREDICT_WRITE_PATH))
    data_predict.to_csv(PREDICT_WRITE_PATH)

if __name__ == '__main__':

  parser = argparse.ArgumentParser()
  parser.add_argument(
      '--verbose', help='Run in verbose mode.', action='store_true')
  parser.add_argument(
      "--train_data", type=str, default="", help="Path to the training data.")
  parser.add_argument(
      "--predict_data", type=str, default="", help="Path to the prediction data.")

  FLAGS, unparsed = parser.parse_known_args()

  main()
