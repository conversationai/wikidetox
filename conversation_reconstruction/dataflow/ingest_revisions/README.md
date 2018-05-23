# Wikipedia Talk Page Ingestion

This folder contains tools for ingesting revisions from a Wikipedia into BigQuery records. 

## Prerequisites

This code is written for Python 2.7.

```
pip install -r requirements.txt
```

## Usage

### Ingestion Utils

See detailed README under ingest_utils.

### Test Ingest Utils

Run
```
python ingester_test.py
```
will test a wikipedia revision in xml format from ingest_utils package for ingestion utilities.


### Generate Batched Input Lists 

In order to divide the full input list with all dumps into batches, run
```
python truncate_input_lists.py
```
This code is used to run locally, please download the full list first and upload the batched input lists in cloud storage mannually.

### Dataflow Pipeline for Ingesting Revisions into BigQuery Records 

In order to ingest talk page revisions into BigQeury records, use:
```
python dataflow_main.py --setup_file ./setup.py 
```
This will ingest from a short list of 10 dumps into BigQuery, if you choose to use optional argument batchno(in the range 0 to 25), you can select a particular batch of dumps you want to run, the ingestor will run the batch of 20 dumps. The input data consists of all the batches and the short list of 10 dumps.
This code is used to run on Google DataFlow pipeline.
