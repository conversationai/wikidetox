#!/bin/bash
gcloud storage rm --recursive gs://wikidetox-viz-dataflow/process_tmp/revs
gcloud storage mv --preserve-acl gs://wikidetox-viz-dataflow/process_tmp/current/* gs://wikidetox-viz-dataflow/process_tmp/next_stage/



