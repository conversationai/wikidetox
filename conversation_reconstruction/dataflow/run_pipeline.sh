#Copyright 2018 Google Inc.
#Licensed under the Apache License, Version 2.0 (the "License");
#you may not use this file except in compliance with the License.
#You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#Unless required by applicable law or agreed to in writing, software
#distributed under the License is distributed on an "AS IS" BASIS,
#WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#See the License for the specific language governing permissions and
#limitations under the License.
#
#-------------------------------------------------------------------------------
# Run Pipeline
#
# This bash script calls functionalities in the conversation reconstruction
# package: 1) downloads the public data dump; 2) ingests the dump data to json
# format; 3) reconstructs conversations from it; 4) cleans the result format.
#
# Specify the language and the dumpdate of the data you want to process, run
# with ./run_pipeline.sh

language=es
dumpdate=20180601

# Download the Dump

cd ingest_revisions
source activate python2
python dataflow_main.py --setup_file ./setup.py --download --ingestFrom=wikipedia --language=${language} --dumpdate=${dumpdate} --cloudBucket=wikidetox-viz-dataflow/raw-downloads/${language}-${dumpdate} || exit 1
source deactivate
cd ..

# Ingest dump into Json

cd ingest_revisions
source activate python2
python dataflow_main.py --setup_file ./setup.py --ingestFrom=cloud --language=${language} --dumpdate=${dumpdate} --cloudBucket=wikidetox-viz-dataflow/raw-downloads/${language}-${dumpdate} --output=gs://wikidetox-viz-dataflow/ingested || exit 1
source deactivate
cd ..

# Initialize Page States

gsutil -m rm -r gs://wikidetox-viz-dataflow/process_tmp_${language}_${dumpdate}/next_stage/*
gsutil -m rm -r gs://wikidetox-viz-dataflow/process_tmp_${language}_${dumpdate}/current/*
gsutil -m rm -r gs://wikidetox-viz-dataflow/process_tmp_${language}_${dumpdate}/bakup/*

gsutil -m cp empty_file gs://wikidetox-viz-dataflow/process_tmp_${language}_${dumpdate}/current/last_rev
gsutil -m cp empty_file gs://wikidetox-viz-dataflow/process_tmp_${language}_${dumpdate}/current/page_states
gsutil -m cp empty_file gs://wikidetox-viz-dataflow/process_tmp_${language}_${dumpdate}/current/error_log

# Start Reconstruction
cd conversation_reconstruction
source activate python2
python dataflow_main.py --input gs://wikidetox-viz-dataflow/ingested/${dumpdate}-${language}/*/revisions*.json --setup_file ./setup.py --output_name ${language}${dumpdate} --process_file process_tmp_${language}_${dumpdate} || exit 1
source deactivate
cd ..

# Move results
gsutil -m rm -r gs://wikidetox-viz-dataflow/process_tmp_${language}_${dumpdate}/revs
gsutil -m mv gs://wikidetox-viz-dataflow/process_tmp_${language}_${dumpdate}/next_stage/ gs://wikidetox-viz-dataflow/wikiconv_v2/${language}-${dumpdate}/page_states
gsutil -m mv gs://wikidetox-viz-dataflow/reconstructed_res gs://wikidetox-viz-dataflow/wikiconv_v2/${language}-${dumpdate}/reconstructed_results

# Clean Result Format
cd conversation_reconstruction
source activate python2
python dataflow_main.py --input gs://wikidetox-viz-dataflow/wikiconv_v2/${language}-${dumpdate}/reconstructed_results --setup_file ./setup.py --output gs://wikidetox-viz-dataflow/wikiconv_v2/${language}-${dumpdate}/cleaned_results || exit 1
source deactivate
cd ..
