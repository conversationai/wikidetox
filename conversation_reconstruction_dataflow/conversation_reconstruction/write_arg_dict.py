import json

bucket = 'gs://cornell-experimental'
arg_dict = {'input':'%s/ingested/enwiki-20170601-pages-meta-history12.xml-p4899708p4972051.json' % bucket, 'output':'%s/conversations/log' % bucket, 'project':'wikidetox', 'runner': 'DataflowRunner', \
'setup_file': './setup.py', \
'staging_location':'%s/staging' % bucket, 'temp_location':'%s/temp' % bucket, \
'job_name':'yiqing-construction-test', 'worker_machine_type':'n1-highmem-4', 'num_workers':'5'}
with open('args_config.json', 'w') as w:
    w.write(json.dumps(arg_dict))
