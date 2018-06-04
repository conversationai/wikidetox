cd ..
python shard.py --category longpages --input gs://wikidetox-viz-dataflow/ingested_long_pages/ingested-*.avro --output gs://wikidetox-viz-dataflow/sharded_ingested_long_pages/ --setup_file ./setup.py


