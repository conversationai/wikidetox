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

set -e  # Exit on failures.
set -x

PHASE1=1  # Download the wikipedia dump.
PHASE2=1  # Injest to JSON
PHASE3=1  # Page conversion
PHASE4=1  # Page conversion

while getopts "1234" opt; do
  case "$opt" in
    1)
      PHASE1=0
      ;;
    2)
      PHASE2=0
      ;;
    3)
      PHASE3=0
      ;;
    4)
      PHASE4=0
      ;;
    h)
      echo "$0 (flags)"
      echo "Specifying -k will skip that phase, eg. -1: skip download."
      exit 0
  esac
done

. config/wikiconv.config
. "${pathToVirtualEnv}/bin/activate"

# Download the Dump

if (( PHASE1 )); then
  cd ingest_revisions
  bazel run :dataflow_main -- \
    --setup_file "${PWD}/setup.py" \
    --download \
    --ingestFrom=wikipedia --language="${language}" --dumpdate="${dumpdate}" \
    --project "${cloudProject}" --bucket "${cloudBucket}"
  cd ..
fi

# Ingest dump into JSON

if (( PHASE2 )); then
  cd ingest_revisions
  bazel run :dataflow_main -- \
    --setup_file "${PWD}/setup.py" \
    --ingestFrom=cloud \
    --language="${language}" --dumpdate="${dumpdate}" \
    --output="gs://${cloudBucket}/ingested" --project "${cloudProject}" \
    --bucket "${cloudBucket}"
  cd ..
fi

if (( PHASE3 )); then
  # Initialize Page States
  gsutil -m rm -r \
    "gs://${cloudBucket}/process_tmp_${language}_${dumpdate}/next_stage/*" \
    "gs://${cloudBucket}/process_tmp_${language}_${dumpdate}/current/*" \
    "gs://${cloudBucket}/process_tmp_${language}_${dumpdate}/bakup/*" || true

  gsutil -m cp empty_file \
    "gs://${cloudBucket}/process_tmp_${language}_${dumpdate}/current/last_revisions/last_rev"
  gsutil -m cp empty_file \
    "gs://${cloudBucket}/process_tmp_${language}_${dumpdate}/current/page_states/page_states"
  gsutil -m cp empty_file \
    "gs://${cloudBucket}/process_tmp_${language}_${dumpdate}/current/error_logs/error_log"

  # Start Reconstruction
  cd conversation_reconstruction
  bazel run :dataflow_main -- \
    --setup_file "${PWD}/setup_dataflow_main.py" \
    --input_state "gs://${cloudBucket}/process_tmp_${language}_${dumpdate}/current" \
    --input_revisions "gs://${cloudBucket}/ingested/${dumpdate}-${language}/*/revisions*.json" \
    --output_state "gs://${cloudBucket}/process_tmp_${language}_${dumpdate}/next_stage" \
    --output_conversations "gs://${cloudBucket}/conversations-${language}${dumpdate}" \
    --runner DataflowRunner \
    --project "${cloudProject}" \
    --max_num_workers 80
  cd ..
fi

if (( PHASE4 )); then
  # Move results
  gsutil -m mv \
    "gs://${cloudBucket}/process_tmp_${language}_${dumpdate}/next_stage/" \
    "gs://${cloudBucket}/wikiconv_v2/${language}-${dumpdate}/page_states"
  gsutil -m mv \
    "gs://${cloudBucket}/conversations-${language}${dumpdate}" \
    "gs://${cloudBucket}/wikiconv_v2/${language}-${dumpdate}/conversations"
  gsutil -m rm -r "gs://${cloudBucket}/process_tmp_${language}_${dumpdate}"

  # Clean Result Format
  cd conversation_reconstruction
  bazel run :dataflow_content_clean -- \
    --setup_file "${PWD}/setup_content_clean.py" \
    --input \
    "gs://${cloudBucket}/wikiconv_v2/${language}-${dumpdate}/conversations/conversations*" \
    --output \
    "gs://${cloudBucket}/wikiconv_v2/${language}-${dumpdate}/cleaned_results/wikiconv-${language}-${dumpdate}-" \
    --error_log="gs://${cloudBucket}/format-clean/error_log_${language}_${dumpdate}-" \
    --jobname="${language}${dumpdate}" --project "${cloudProject}" --bucket "${cloudBucket}"
  cd ..
fi

deactivate
