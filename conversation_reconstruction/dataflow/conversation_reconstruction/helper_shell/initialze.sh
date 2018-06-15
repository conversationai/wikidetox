#!/bin/bash
gsutil -m rm gs://wikidetox-viz-dataflow/process_tmp/next_stage/*
gsutil -m rm gs://wikidetox-viz-dataflow/process_tmp/current/*
gsutil -m rm gs://wikidetox-viz-dataflow/process_tmp/bakup/*

gsutil -m cp empty_file gs://wikidetox-viz-dataflow/process_tmp/next_stage/last_rev
gsutil -m cp empty_file gs://wikidetox-viz-dataflow/process_tmp/next_stage/page_states
gsutil -m cp empty_file gs://wikidetox-viz-dataflow/process_tmp/next_stage/error_log




