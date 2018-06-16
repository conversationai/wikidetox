cd ..
gsutil -m mv -p gs://wikidetox-viz-dataflow/process_tmp/shortpages/* gs://wikidetox-viz-dataflow/process_tmp/shortpages_bakup/
gsutil -m mv -p gs://wikidetox-viz-dataflow/process_tmp/next_shortpages/* gs://wikidetox-viz-dataflow/process_tmp/shortpages/
python dataflow_main.py --category shortpages --input gs://wikidetox-viz-dataflow/sharded_ingested_short_pages/date-{year}/revisions-week*.avro --week 1 --year 2017 --setup_file ./setup.py

