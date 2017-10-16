# Predicting Conversations Going Bad

This is the package for the machine learning task predicting conversations going bad. The conversations are matched in bigquery and downloaded to local storage.

To run the prediction task:
- data_cleansing/get_data.py will prepare the data for feature extraction
- feature_extraction/feat_extraction.py will extract the features needed in the machine learning task
- data_cleansing/get_train_data.py will randomly split the data into train, develop and test splits.

Run the prediction task in Prediction Task.ipynb
