cd ..
gsutil -m mv -p gs://wikidetox-viz-dataflow/process_tmp/current/* gs://wikidetox-viz-dataflow/process_tmp/bakup/
gsutil -m mv -p gs://wikidetox-viz-dataflow/process_tmp/next_stage/* gs://wikidetox-viz-dataflow/process_tmp/current/

python dataflow_main.py --input gs://wikidetox-viz-dataflow/ingested/latest-ch/date-11at2007/revisions*.json --week 11 --year 2007 --setup_file ./setup.py --testmode
