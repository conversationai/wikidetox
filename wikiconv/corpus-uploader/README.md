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
mkdir -p config/
rsync --ignore_existing figshare_token.template.config config/figshare_token.config
```

2. Create [a figshare personl token](https://figshare.com/account/applications),
and enter it into the copy of the template file in your config directory
(`config/figshare_token.config`).

3. Set the language you want to create a corpus for in the `config/figshare_token.config` file.

4. Run `upload.sh`

Note: for large uploads this can be slow; approx a week for the English corpus.

TODO: rewrite in nodejs so that we can *easily* support concurrent uploads,
restarting, command line flags for language, and stream directly from google
cloud file to Figshare. This should speed things up considerably, estimated
probably 20x speedup.

## Kaggle:

1. To upload the data, you will need to have a [kaggle authentication token
setup](https://www.kaggle.com/docs/api)

TODO: complete scripts for this.
