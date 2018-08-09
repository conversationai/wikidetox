# Conversation Constructor for Wikipedia Talk Pages

This package contains reconstruction tools to extract the conversation structure
from Wikipedia talk pages.
Please note that this package used Python 2.7.

You can find the Wikipedia [research
showcase](https://www.mediawiki.org/wiki/Wikimedia_Research/Showcase#June_2018) that explains the effort of
creating this dataset. The corresponding slides can be found
[here](slides/WikiConv\ --\ wikishowcase.pdf).

This reconstruction tool aims to show the wikipedia conversations with its full
history; namely also including not just new posts, but also modifications, 
deletions and reverts to them.
For example, rather than showing a snapshot of the conversation as in

![Figure1](slides/original_conv.png)

The resulted the dataset includes all the actions led to it, as shown in

![Figure2](slides/reconstructed.png).

## Setup the environment

In the *current directory*:

- Follow the steps in section 1 to set up [your cloud project](https://cloud.google.com/dataflow/docs/quickstarts/quickstart-python). Note that *do not proceed* to install the newest google cloud dataflow, which may be in-compatible with some of the packages listed in requirements.txt.
- Use your service account to set up boto:
  `gsutil config -e`
- Setup your python environment:
    - Set up a [virtualenv environment](https://packaging.python.org/guides/installing-using-pip-and-virtualenv/)
    - Do . /path/to/directory/bin/activate
    - pip install -r requirements.txt

## Run the pipeline
- Copy template.config to config/wikiconv.config using
```
rsync --ignore-existing ./template.config ./config/wikiconv.config
```
- Fill in your own configuration.
- Run run_pipeline.sh.
