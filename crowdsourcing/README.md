# Crowdsourcing Experiment

There are three respositories to setup:

* `crowd9-api` - is used to serve data to be crowdsourced.
* `crowd9-demo-server` - is used to serve a specific crowdsourcing dataset.
* `crowd9-demo-webapp` - is the frontend used by `demo-server`.

## Concepts

The crowdsourcing tool is backed by by a Spanner Database. The database consists
of:

* `questions` - Holds all questions. Some questions are for training crowdworkers (`training` questions), some for testing crowdworkers (`test` questions), and others - typically most - are for getting answers from crowdworkers and for which the 'correct' answers is not known (`toanswer` questions). When being used for simple crowdsourced labelling, there are only `toansawer` questions.
* `client_jobs` - Meta data for a job given which is available to a client. Each job specifies a set of questions in the `question` table (by `client_jobs.question_group_id = questions.question_group_id`), and expects a number of answers per question which will end up living in the `answer table`.
* `answers` - Holds all answers to questions submitted by crowdsourcing. Each row in this table is associated to a particular `client_job` (by `client_jobs.client_job_key = answers.client_job_key`) and question (by `answers.question_id = questions.question_id`). There may be many `answers` rows per `client_job_key` and `question_id`.

When being used to support third-party crowd-sourcing apps, where `test` and `training` questions are relevant, there is also a fourth table:

* `question_scoring` - Each possible answer for a question can have a record here that maps it to a 'score'. This is intended to provide the ability to have a flexible way to score a crowd-workers answers to questions.


## Pre-requisits

Assumes basic development tools like git, xcode (if on Mac), etc are installed.

* Install [Google Cloud SDK](https://cloud.google.com/sdk/)
* Install node (recommended to use the [Node Version Manager (nvm)](https://github.com/creationix/nvm/blob/master/README.md#installation).
* Install `yarn` (to install dependencies), `mocha` (for testing), and `typescript` and `ts-node` for running TypeScript Scripts, by running the command `npm install -g yarn mocha typescript ts-node`


## Setup the cloud project which is going to be used

Create a cloud project, setup
[spanner](https://pantheon.corp.google.com/spanner/instances/crowdsource/databases)
as per the instructions in the `crowd9-api` directory.

To run the database creation script you'll also need to have setup a service
account key with `Compute Engine default service account` credentials, which
you can do from:
https://pantheon.corp.google.com/apis/credentials/serviceaccountkey
See the top of the file `crowd9-api/src/setup/create_db.ts` for more details.



## Setup of the repositories:

Setup API:

```bash
cd crowd9-api
yarn install
yarn run setup
# Now edit the crowd9-api/build/config/server_config.json file.
yarn run build
cd ..
```

Now look at the `crowd9-api/docs/example_curl_interactions`


Setup the demo server:

```bash
cd crowd9-demo-server
yarn install
yarn run setup
# Now edit the crowd9-demo-server/build/config/server_config.json file
yarn run build
cd ..
```


Setup the webapp:

```bash
cd crowd9-demo-webapp
yarn install
yarn run build
cd ..
```

This is pure HTML/CSS/JS, and will actually be served by the
`crowd9-demo-server`, so copy the webapp production build to the
`crowd9-demo-server`'s static directory:

```bash
cp crowd9-demo-webapp/dist/* crowd9-demo-server/static/
```

Now you can deploy the `crowd9-api` and `crowd9-demo-server`.

You can also run them locally, although you'll need to change the port of
the `crowd9-demo-server` and also tell is to talk to localhost to speak your
local `crowd9-api` service.
