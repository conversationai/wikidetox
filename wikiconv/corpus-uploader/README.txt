# WikiConv Corpus Uploader

Because the corpus consists of over 500 files and 500GB of data, we need some
scripts to actually upload it to Kaggle and Figshare.

This assumes that your dataset has been computed on Google Cloud Compute, and
the data is living in a google cloud storage buket, something like:

https://console.cloud.google.com/storage/browser/wikidetox-wikiconv-public-dataset

## Figshare:

1. Make a copy of the token template file, and place it into a local `config`
directory:

```
mkdir -p config
rsync --ignore_existing figshare_token.template.py config/figshare_token.py
```

2. Create [a figshare personl token](https://figshare.com/account/applications),
and enter it into the copy of the template file in your config directory
(`config/figshare_token.py`).

3.

## Kaggle:

1. To upload the data, you will need to have a [kaggle authentication token setup]()
