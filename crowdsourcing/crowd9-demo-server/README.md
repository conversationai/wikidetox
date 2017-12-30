# ConversationAI Crowd9 Demo Server

This directory contains a simple server intended illustrate how one might build a crowsdsourcing app using the prototype crowd9-api.

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

Link in the Wikipedia conversations library (to treat it as a node package):

```shell
cd node_modules
ln -s ../../wpconvlib ./
cd ..
```

### Setup the config file

Before you can deploy, you need to:

1. Copy the `server_config.template.json` file to `build/config/server_config.json`.
2. In the `build/config/server_config.json` file, set these values:

    * `cloudProjectId` This is the name of your google cloud project.
    * `clientJobKey` This is a client job key to access the crowd9api.
    * `crowd9ApiUrl` This should be the URL of the crowd9api server.

### Deployment to Google Cloud Project

This project uses appengine flexible environment for deployment, which is configured in the `app.yml` file.

To deploy, make sure your cloud project is set appropriately, and run;

```
gcloud app deploy
```

## Testing with curl

```
export SERVER=...
curl -H "Content-Type: application/json" -X GET ${SERVER}/work
```

## Development

To start a local dev server:

```
yarn run start:watch
```

This will also watch all the files, rebuilding and restarting the server when anything
changes.

## About this code

This repository contains example code to help experimentation with the Perspective API; it is not an official Google product.
