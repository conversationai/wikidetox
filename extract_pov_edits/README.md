# Wikipedia Talk Page Ingestion

This folder contains tools for ingesting revisions from a Wikipedia into Cloud
storage in json formats.

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


### Dataflow Pipeline for Ingesting Revisions into BigQuery Records 

Ingests talk page revisions into json records using dataflow pipeline, 
use dataflow_main.py.
Detailed information about arguments can be seen in dataflow_main.py.
