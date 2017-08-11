# Getting Wikipedia Revisions

This folder contains tools for downloading revisions from a Wikipedia dump and ingesting them into a json file.

## Prerequisites

This code is written for Python 2.7.

## Usage

### Step 1: Downloading Wikipedia Revisions

In order to download the Wikipedia revisions from a dump, use:

```
python wikipedia_revisions_download.py --wikidump_url_root <path-to-dump> --output_dir <path-to-output>
```

Both arguments are optional and if a dump is not provided, the default will be 
https://dumps.wikimedia.org/enwiki/20170601/

The revisions will be stored in chunks as 7z files in the specified output directory.

### Step 2: Ingesting Revisions to .json

The dumps are stored as xml files. We can reformat these to .json with:

```
python wikipedia_revisions_ingester.py --input <path-to-input-7z-chunk>
```

Note that the output is written to stdout and so should be redirected to an appropriate output file. 

### Step 3: Filter out non-talk-page data

Filtered out non-talk-page data.

```
python wikipedia_revisions_ingester.py --input <path-to-input-7z-chunk> | filter.py 
```
Same as the last step, note that the output is written to stdout and so should be redirected to an appropriate output file. 


