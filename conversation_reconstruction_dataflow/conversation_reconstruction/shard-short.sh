#python shard.py --category shorpages --input gs://wikidetox-viz-dataflow/sharded_ingested_short_pages/date-2017/revisions-1.avro --output gs://wikidetox-viz-dataflow/sharded_ingested_short_pages/ --setup_file ./setup.py
python shard.py --category shortpages --input gs://wikidetox-viz-dataflow/ingested_short_pages/ingested-*.avro --output gs://wikidetox-viz-dataflow/sharded_ingested_short_pages/ --setup_file ./setup.py


