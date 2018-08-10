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

. config/wikiconv.config

# Download the Dump

cd ingest_revisions
. ${pathToVirtualEnv}/bin/activate
python dataflow_main.py --setup_file ./setup.py --download --ingestFrom=wikipedia --language=${language} --dumpdate=${dumpdate} --cloudBucket=${cloudBucket}/raw-downloads/${language}-${dumpdate} --project ${cloudProject} --bucket ${cloudBucket}|| exit 1
deactivate
cd ..

# Ingest dump into Json

cd ingest_revisions
. ${pathToVirtualEnv}/bin/activate
python dataflow_main.py --setup_file ./setup.py --ingestFrom=cloud --language=${language} --dumpdate=${dumpdate} --cloudBucket=${cloudBucket}/raw-downloads/${language}-${dumpdate} --output=gs://${cloudBucket}/ingested --project ${cloudProject} --bucket ${cloudBucket}|| exit 1
deactivate
cd ..

# Initialize Page States

gsutil -m rm -r gs://${cloudBucket}/process_tmp_${language}_${dumpdate}/next_stage/*
gsutil -m rm -r gs://${cloudBucket}/process_tmp_${language}_${dumpdate}/current/*
gsutil -m rm -r gs://${cloudBucket}/process_tmp_${language}_${dumpdate}/bakup/*

gsutil -m cp empty_file gs://${cloudBucket}/process_tmp_${language}_${dumpdate}/current/last_rev
gsutil -m cp empty_file gs://${cloudBucket}/process_tmp_${language}_${dumpdate}/current/page_states
gsutil -m cp empty_file gs://${cloudBucket}/process_tmp_${language}_${dumpdate}/current/error_log

# Start Reconstruction
cd conversation_reconstruction
. ${pathToVirtualEnv}/bin/activate
python dataflow_main.py --input gs://${cloudBucket}/ingested/${dumpdate}-${language}/date-201[6-8]/revisions*.json --setup_file ./setup.py --output_name ${language}${dumpdate} --process_file process_tmp_${language}_${dumpdate} --project ${cloudProject} --bucket ${cloudBucket}|| exit 1
deactivate
cd ..

# Move results
gsutil -m mv gs://${cloudBucket}/process_tmp_${language}_${dumpdate}/next_stage/ gs://${cloudBucket}/wikiconv_v2/${language}-${dumpdate}/page_states
gsutil -m rm -r gs://${cloudBucket}/process_tmp_${language}_${dumpdate}
gsutil -m mv gs://${cloudBucket}/reconstructed_res/reconstruction-pages-${language}${dumpdate} gs://${cloudBucket}/wikiconv_v2/${language}-${dumpdate}/reconstructed_results

# Clean Result Format
cd conversation_reconstruction
. ${pathToVirtualEnv}/bin/activate
python dataflow_content_clean.py --input gs://${cloudBucket}/wikiconv_v2/${language}-${dumpdate}/reconstructed_results/*/revisions* --setup_file ./setup.py --output gs://${cloudBucket}/wikiconv_v2/${language}-${dumpdate}/cleaned_results/wikiconv-${language}-${dumpdate}- --error_log=gs://${cloudBucket}/format-clean/error_log_${language}_${dumpdate}- --jobname=${language}${dumpdate} --project ${cloudProject} --bucket ${cloudBucket} || exit 1
deactivate
cd ..
