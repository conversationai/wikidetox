import json

arg_dict = {'input':'$BUCKET/ingested/enwiki-20170601-pages-meta-history*.json' , 'output':'$BUCKET/conversations/', 'project':'wikidetox-viz', 'runner': 'DataflowRunner', 'setup_file': './setup.py', 'extra_package':'construct_utils', \
'staging_location':'$BUCKET/staging', 'temp_location':'$BUCKET/temp' }
with open('arg_config.json', 'w') as w:
    w.write(json.dumps(arg_dict))
