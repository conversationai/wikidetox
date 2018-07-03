#!/bin/bash
cd ..
python dataflow_reshard_input.py --input gs://wikidetox-viz-dataflow/ingested/en-20180501/20180501-en/*/revisions*.json --setup_file ./setup.py
