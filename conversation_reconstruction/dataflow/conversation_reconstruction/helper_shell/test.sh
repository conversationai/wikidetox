cd ..
python dataflow_main.py --input gs://wikidetox-viz-dataflow/ingested/latest-ch/date-11at2007/revisions*.json --week 11 --year 2007 --setup_file ./setup.py --testmode
