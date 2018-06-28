cd ..
gsutil -m rm -r gs://wikidetox-viz-dataflow/process_tmp/revs
gsutil -m mv -p gs://wikidetox-viz-dataflow/process_tmp/current/* gs://wikidetox-viz-dataflow/process_tmp/bakup/
gsutil -m mv -p gs://wikidetox-viz-dataflow/process_tmp/next_stage/* gs://wikidetox-viz-dataflow/process_tmp/current/
echo "start job on week $i $y"
python dataflow_main.py --input gs://wikidetox-viz-dataflow/ingested/en-20180501/20180501-en/date-3[7-9]at2008/revisions*.json --setup_file ./setup.py --output_name 37to39at2008 --process_file process_tmp || exit
