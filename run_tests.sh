#!/bin/bash

(cd wikiconv/ingest_revisions; bazel test --test_output=streamed ...)

(cd wikiconv/conversation_reconstruction; bazel test --test_output=streamed ...)
