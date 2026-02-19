#!/bin/bash
gcloud storage rm --recursive gs://wikidetox-viz-dataflow/process_tmp/next_stage/*
gcloud storage rm --recursive gs://wikidetox-viz-dataflow/process_tmp/current/*
gcloud storage rm --recursive gs://wikidetox-viz-dataflow/process_tmp/bakup/*

gcloud storage cp empty_file gs://wikidetox-viz-dataflow/process_tmp/next_stage/last_rev
gcloud storage cp empty_file gs://wikidetox-viz-dataflow/process_tmp/next_stage/page_states
gcloud storage cp empty_file gs://wikidetox-viz-dataflow/process_tmp/next_stage/error_log




