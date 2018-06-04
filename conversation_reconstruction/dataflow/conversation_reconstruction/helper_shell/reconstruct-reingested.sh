cd ..
for i in $(seq 1 53)
do
#    gsutil -m rm gs://wikidetox-viz-dataflow/process_tmp/reingested_bakup/*
    gsutil -m mv -p gs://wikidetox-viz-dataflow/process_tmp/reingested/* gs://wikidetox-viz-dataflow/process_tmp/reingested_bakup/
    gsutil -m mv -p gs://wikidetox-viz-dataflow/process_tmp/next_reingested/* gs://wikidetox-viz-dataflow/process_tmp/reingested/
    echo "start job on week $i"
    python dataflow_reingested.py --category reingested --input gs://wikidetox-viz-dataflow/reingested/date-{week}at{year}/revisions*.json --week $i --year 2017 --setup_file ./setup.py 
done



