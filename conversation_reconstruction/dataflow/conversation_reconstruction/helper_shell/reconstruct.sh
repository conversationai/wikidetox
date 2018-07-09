cd ..
for year in $(seq 2011 2018)
do
   gsutil -m rm -r gs://wikidetox-viz-dataflow/process_tmp/revs
   gsutil -m mv -p gs://wikidetox-viz-dataflow/process_tmp/current/* gs://wikidetox-viz-dataflow/process_tmp/bakup/
   gsutil -m mv -p gs://wikidetox-viz-dataflow/process_tmp/next_stage/* gs://wikidetox-viz-dataflow/process_tmp/current/
   echo "start job on year $year"
   source activate python2
   python dataflow_main.py --input gs://wikidetox-viz-dataflow/ingested/en-20180501/20180501-en/date-*at$year/revisions*.json --setup_file ./setup.py --output_name $year --process_file process_tmp || exit
   source deactivate
done
