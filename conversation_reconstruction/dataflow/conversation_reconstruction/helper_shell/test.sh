cd ..
gsutil rm gs://wikidetox-viz-dataflow/test_tmp/current/*
gsutil -m cp helper_shell/empty_file gs://wikidetox-viz-dataflow/test_tmp/current/last_rev
gsutil -m cp helper_shell/empty_file gs://wikidetox-viz-dataflow/test_tmp/current/page_states
gsutil -m cp helper_shell/empty_file gs://wikidetox-viz-dataflow/test_tmp/current/error_log
python dataflow_main.py --input gs://wikidetox-viz-dataflow/ingested/en-20180501/20180501-en/date-5at2001/revisions*.json --week 5 --year 2001 --setup_file ./setup.py --process_file test_tmp --output_name test --testmode
