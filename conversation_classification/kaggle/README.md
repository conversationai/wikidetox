# Toxic Comment Classification Kaggle Challenge

This directory is a place to play around with solutions for the [Toxic Comment Classification Kaggle challenge](https://www.kaggle.com/c/jigsaw-toxic-comment-classification-challenge). The challenge was created by the Jigsaw Conversation AI team in December 2017
and the it ends in February 2018.

These models are meant to be simple baselines created independently from the Google infrastructure.

## To Run
1. Download the training (`train.csv`) and test (`test.csv`) data from the
[Kaggle challenge](https://www.kaggle.com/c/jigsaw-toxic-comment-classification-challenge/data).
2. Install library dependencies:
```shell
pip install -r requirements.txt
```

3. Run a model on a given class (e.g. 'toxic' or 'obscene'):

```shell
python model.py --train_data=train.csv --predict_data=test.csv --y_class=toxic --model=bag_of_words
```

## Available Models
  * `bag_of_words` - bag of words model with a learned word-embedding layer

More to come!