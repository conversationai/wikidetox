# WikiConv Corpus Uploader

Because the corpus consists of over 500 files and 500GB of data, we need some
scripts to actually upload it to Kaggle and Figshare.

This assumes that your dataset has been computed on Google Cloud Compute, and
the data is living in a google cloud storage buket, something like:

https://console.cloud.google.com/storage/browser/wikidetox-wikiconv-public-dataset

## Figshare

The `./ts-bin/figshare-uploader.ts` file is a typescript nodejs tool that uses
the [Figshare API](https://docs.figshare.com/) to upload files to Figshare
articles from [Google Cloud Storage](https://cloud.google.com/storage/).

Usage:

1. Make a copy of the token template file, and place it into a local `config`
   directory:

```bash
mkdir -p config/
rsync --ignore_existing config.template.ts config/config.ts
```

1. Create [a figshare personl token](https://figshare.com/account/applications),
   and enter it into the copy of the template file in your config directory
   (`config/config.ts`).

1. Set the languages you want to upload to figshare in the `config/config.ts`
   file.

1. Run `ts-node ./ts-bin/figshare-uploader.ts`

The script will tell you about any missing files (in cloud storage but not
having an entry in the Figshare article). The script skips all existing
files/parts that are uploaded, and only uploads new parts that were missing. It
takes a parameter `--concurrently=N` where `N` is a number for the concurrent
uploads to use (default is 5). It is safe to cancel the script and restart it.

TODO: make the script create new articles/files for files in cloud storage that
are needed. For the wikiconv corpus, we created the files using the
`old/upload.sh` script, but it fails to actually upload the parts.

### Description of Figshare things here

* `ts-lib/figshare_types.ts` contains common types for the JSON objects returned
  by the Figshare API.
* `ts-lib/cloud_storage_util.ts` provides a couple of helper functions for
  working with Google Cloud storage.
* `ts-lib/util.ts` provides some helper funcions (some set operations, sleep,
  and pretty printing)

## Kaggle

1. To upload the data, you will need to have a [kaggle authentication token
   setup](https://www.kaggle.com/docs/api)

TODO: complete scripts for this.
