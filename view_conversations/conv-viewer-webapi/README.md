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

### Config file setup

Before you can deploy, you need to:

1. Copy the `server_config.template.json` file to `build/config/server_config.json`.
2. In the `build/config/server_config.json` file, set these values:

    * `cloudProjectId` This is the name of your google cloud project.

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
gcloud app deploy
```

## Development

To start a local dev server:

```
yarn run serve:watch
```

This will also watch all the files, rebuilding and restarting the server when anything
changes.

## About this code

This repository contains example code to help experimentation with the Perspective API; it is not an official Google product.
