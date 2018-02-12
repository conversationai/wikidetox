#!/bin/bash

JOB_NAME=test_kaggle_training
REGION=us-central1

DATE=`date '+%Y%m%d_%H%M%S'`
OUTPUT_PATH=gs://kaggle-model-experiments/$JOB_NAME_$DATE

echo $OUTPUT_PATH

gcloud ml-engine local train \
     --module-name=trainer.model \
     --package-path=trainer \
     --job-dir=model -- \
     --train_data=gs://kaggle-model-experiments/train.csv \
     --predict_data=gs://kaggle-model-experiments/test.csv \
     --y_class=toxic \
     --train_steps=100
