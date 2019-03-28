# wikiviz-v2

Version 2 of the WikiDetox visualization.

The visualization uses the [Perspective API](http://www.perspectiveapi.com/) to score Wikipedia discussion comments, via an express server.

This static part of the project was generated with [Vue CLI](https://cli.vuejs.org/) version 3.0.5.

## Package Management

This project uses [Yarn](https://yarnpkg.com) for package mangement. Install with `npm install -g yarn`. 
In order to run the project you will need [Vue CLI](https://cli.vuejs.org/ installed globally eg. `yarn add @vue/cli -g`

## Project setup

To run code using your local machine (not via the docker
environment), you will need to install `nodejs` (e.g., by [installing NVM](https://github.com/creationix/nvm)).
From project root, run

```
yarn install
```
to install dependencies and create a `yarn.lock` file.

This project relies on Google's [BigQuery API](https://cloud.google.com/bigquery/docs/reference/rest/v2/) to query data, via an express server. To setup an instance you need a Google Cloud Project with the Perpsective API enabled.

1. Download a service account key under API access in your cloud project, and store it in root folder
2. Go to server/config.ts and enter the `gcloudKey` and `API_KEY` fields with a path to a keyfile for google cloud access, and a Perspective API key respectively.

## Development server that watches Vue project

To run a local server, run:
```
yarn run start:dev
```
This command will start an express server at `localhost:8080` that fetches bigquery data, and a Vue server that watches local Vue.js changes at `localhost:8081`.

To watch typescript file changes in server folder, run `watch-server`. This command will build the `server/*.ts` files on file change. You will need to start the dev server again after file build, for changes to take effect. 

## Build files 

To build files for production, run:
```
yarn run build
```

## Production server that uses compiled sources

To run server on compiled sources, run:
```
yarn run start:prod
```
This command will start serving files from `build/` folder at `localhost:8080`.

## Lints and fixes files

To perform lint over Vue.js files, run:
```
yarn run lint
```

## Project deployment

# Deploy to gcloud

Ensure your shell is logged into cloud platform for deployment:

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_NAME
```

Add a line to your Dockerfile pointing to your gcloud key file: 
```
COPY [keyfilename].json /app/[keyfilename].json
```

Deploy for testing at `dev-dot-YOUR_PROJECT_NAME.appspot-preview.com`:
```bash
gcloud app deploy app.yaml -v dev
```

Deploy to production environment

```bash
# Use the --no-promote flag to ensure you can test before migrating traffic.
gcloud app deploy app.yaml --no-promote
```
