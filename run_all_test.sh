#!/bin/bash
set -e

python -m antidox.wikiwatcher_test
python -m antidox.perspective_test
python -m wikiconv.ingest_revisions.dataflow_tester
python -m wikiconv.conversation_reconstruction.construct_utils.conversation_constructor_test
python -m wikiconv.conversation_reconstruction.construct_utils.reconstruct_conversation_test
python -m wikiconv.conversation_reconstruction.dataflow_test
