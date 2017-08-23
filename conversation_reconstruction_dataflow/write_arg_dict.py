import json

bucket = 'gs://wikidetox-viz-dataflow'
arg_dict = {'input':'%s/ingested/enwiki-20170601-pages-meta-history11.xml-p3924468p3926861.json' % bucket, 'output':'%s/conversations/log' % bucket, 'project':'wikidetox-viz', 'runner': 'DataflowRunner', \
'setup_file': './setup.py', \
'staging_location':'%s/stages' % bucket, 'temp_location':'%s/tempfiles' % bucket, \
'job_name':'yiqing-construction-job-2', 'worker_machine_type':'n1-highmem-4', 'num_workers':'6'}
with open('args_config.json', 'w') as w:
    w.write(json.dumps(arg_dict))
