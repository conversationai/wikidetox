#!/bin/bash
gsutil -m rm -r gs://wikidetox-viz-dataflow/process_tmp/revs
gsutil -m mv -p gs://wikidetox-viz-dataflow/process_tmp/current/* gs://wikidetox-viz-dataflow/process_tmp/next_stage/




