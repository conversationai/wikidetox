cd ..
for i in $(seq 1 53)
do
#    gsutil -m rm gs://wikidetox-viz-dataflow/process_tmp/longpages_bakup/*
    gsutil -m mv -p gs://wikidetox-viz-dataflow/process_tmp/longpages/* gs://wikidetox-viz-dataflow/process_tmp/longpages_bakup/
    gsutil -m mv -p gs://wikidetox-viz-dataflow/process_tmp/next_longpages/* gs://wikidetox-viz-dataflow/process_tmp/longpages/
    echo "start job on week $i"
    python dataflow_main.py --category longpages --input gs://wikidetox-viz-dataflow/sharded_ingested_long_pages/date-{week}at{year}/revisions-*.avro --week $i --year 2017 --setup_file ./setup.py 
done



