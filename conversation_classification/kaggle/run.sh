#!/bin/bash

JOB_NAME=test_kaggle_training
REGION=us-central1

DATE=`date '+%Y%m%d_%H%M%S'`
OUTPUT_PATH=gs://kaggle-model-experiments/${DATE}

echo $OUTPUT_PATH

# Remote
gcloud ml-engine jobs submit training ${JOB_NAME}_${DATE} \
    --job-dir $OUTPUT_PATH \
    --runtime-version 1.4 \
    --module-name trainer.model \
    --package-path trainer/ \
    --region $REGION \
    --verbosity debug \
    -- \
    --train_data gs://kaggle-model-experiments/train.csv \
    --y_class toxic \
    ---predict_data gs://kaggle-model-experiments/test.csv \
    --train-steps 1000 \
    --model cnn \
