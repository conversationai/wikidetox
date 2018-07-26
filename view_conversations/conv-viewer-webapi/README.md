# ConversationAI - Wikidetox Conversation Viewer API

This directory contains an experimental api to supporting viewing conversations on Wikipedia talk pages.

## Setup

This project assumes you have [a Google Cloud Project setup](https://cloud.google.com/) setup; you need
that for deployment.

### Installing Dependencies

Global node dependencies for development: gcloud, node (suggest you use nvm to install it) are [typescript](https://www.typescriptlang.org/) to write sensible JS code, and [yarn](https://yarnpkg.com/lang/en/), and of course node (which is usually most easily installed and managed using [nvm](https://github.com/creationix/nvm/blob/master/README.md)):

After you have installed node/npm using nvm, you can install the other global dependencies using:

```
npm install -g typescript yarn
```

Then from this directory, use yarn to install the local package dependencies:

```
yarn install
```

### Troubleshooting yarn installing failure

If there's grpc installing error occurred during yarn install,

Run

```
nvm i v8 --reinstall-packages-from=default
nvm alias default v8
nvm use default
rm -rf node_modules/
npm i
```
to upgrade to node version 8.

### Config file setup

Before you can deploy, you need to:

1. Copy the `server_config.template.json` file to `build/config/server_config.json`.
2. In the `build/config/server_config.json` file, set these values:

    * `bigQueryProjectId` : The Google Cloud Project ID that contains the BigQuery database.
    * `bigQueryDataSetId` : The name of the dataset in the cloud project.
    * `bigQueryTable` : The name of the table that contains the conversations.

TODO(ldixon): in future we'll move to using OAuth and project credentials.

### Cloud project setup

Set your cloud project name:

```
gcloud config set project ${YOUR_CLOUD_PROJECT_ID}
```

### Deployment to Google Cloud Project

This project uses appengine flexible environment for deployment, which is configured in the `app.yml` file.

To deploy, make sure your cloud project is set appropriately, and run;

```
yarn run build
gcloud app deploy
```

## Development

To start a local dev server:

```
yarn run serve:watch
```

This will also watch all the files, rebuilding and restarting the server when anything
changes.

# Usage as an iFrame for CrowdSourcing


To get see a comment without context:

```
${URL_TO_SERVER}/#{"searchBy":"Comment ID","searchFor":"544184471.16379.16379","embed":true,"showPageContext":false}
```

To get see a comment in conversation with full context:

```
${URL_TO_SERVER}/#{"searchBy":"Conversation ID","searchFor":"114992878.0.0","embed":false",showPageContext":true}
```

This assumes that the conversation actions have a field called `comment_to_highlight`, that is set for the action to highlight, and for that action it is set as it's own ID.

You can also specify a highlight ID in the URL, e.g.:

```
${URL_TO_SERVER}/#{"searchBy":"Conversation ID","searchFor":"543966266.15553.15553","embed":false,"showPageContext":true,"highlightId":"543966266.15553.15553"}
```

## About this code

This repository contains example code to to support Conversation AI research; it is not an official Google product.
