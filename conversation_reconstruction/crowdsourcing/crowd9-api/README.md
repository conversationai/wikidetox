# ConversationAI Crowdsource

This repository is contains an experiment to support crowdsourcing for labelling
comments.

## Setup

This project assumes you have [a Google Cloud Project setup]() setup; you need
that to deploy an instance of the this crowdsourcing service.

### Repository Setup

Global node dependencies for development: gcloud, node (suggest you use nvm to install it),

```
npm install -g typescript yarn
```

```
yarn install
```

Link in the Wikipedia conversations library (to treat it as a node package):

```shell
cd node_modules
ln -s ../../wpconvlib ./
cd ..
```

### Config file setup

Before you can deploy, you need to

Copy the `server_config.template.json` file to `build/config/server_config.json`. You will need to set these values:

* `cloudProjectId` This is the name of your google cloud project.
* `spannerInstanceId` This is your google cloud project's spanner instance name (the service than runs your spanner database)
* `spannerDatabaseName` This is the name of a spanner database in your instance that will hold the tables.
* `adminKey` This is a secret key that will be used to perform administrative actions. In particular, you should create an secret value for `adminKey`. e.g. using output of the command:
    ```
    dd if=/dev/urandom bs=1 count=32 | base64
    ```

TODO(ldixon): in future we'll move to using OAuth and project credentials.

### Cloud project setup

Set your cloud project name:

```
gcloud config set project ${YOUR_CLOUD_PROJECT_ID}
```

Create a spanner instance, e.g. named `crowdsource`:

```
gcloud spanner instances create crowdsource --config=regional-us-central1 \
--description="For Crowd9 Hackathon" --nodes=1
```

Create a GCE instance with spanner scope for the `crowdsource` spanner instance:

```
 gcloud compute instances create --scopes="https://www.googleapis.com/auth/cloud-platform,https://www.googleapis.com/auth/compute,https://www.googleapis.com/auth/compute.readonly" crowdsource
```

Now create a spanner database in the `crowdsource` instance, and the schema for the tables to hold data for this app:

```
node src/setup/create_db.js
```

Note: at any point you can delete the DB and run this script again.

TODO(ldixon): generalize script above to take use env-vars for instance and dbname.

### GCloud project deployment

This project uses appengine flexible environment for deployment, which is configured in the app.yml file.

To deploy, make sure your cloud project is set appropriately, and run;

```
gcloud app deploy
```

## Development

To start a dev server, but also watch all the files and rebuild and restart the server when anything
changes, use:

```
yarn run start:watch
```

## Design

### Tables

 * `questions` - Holds all questions. Some questions are for training crowdworkers, some for testing crowdworkers, and for some (most) for getting answers from crowdworkers and for which the 'correct' answers is not known.
 * `client_jobs` - Meta data for a job given which is available to a client. Each job specifies a set of questions in the `question` table (by `client_jobs.question_group_id = questions.question_group_id`), and expects a number of answers per question which will end up living in the `answer table`.
 * `answers` - Holds all answers to questions. Each row in this table is associated to a particular `client_job` (by `client_jobs.client_job_key = answers.client_job_key`) and `questions` (by `answers.question_id = questions.question_id`). There may be many `answers` rows per `client_job_key` and `question_id`.

#### Questions Table

Table name: `questions`

| Field name                 | Description     |
|----------------------------|-----------------|
| question_id : string       | Unique id for this question |
| question_group_id : string | An identifier for a set of questions to ask crowdworkers. |
| question : string          | A JSON representation for the question |
| type  : string             | One of `test` (for secret questiosn used to test crowdworker quality), `train` (shown to crowdworkers to help them understand the problem, and potentially to screen for crowdworker quality), `to_answer` (questions without answers, which crowdworkers are to contribute answers) |
| accepted_answers : string  |  if `type` is `test` or `train` then this field is a JSON representation for the acceptible answers to the question; if `type` is `to_answer` then this field should be `NULL` |

#### Client Jobs Table

Table name: `client_jobs`

| Field name                    | Description     |
|-------------------------------|-----------------|
| client_job_key : string       | Unique ID for a job given to a crowdsourcing API client to be able to send rows. |
| title : string             | A human readable summary title for the question group |
| description : string       | A detailed description of the question group |
| answers_per_question : string | The number of crowd-workers who should answer each question. |

#### Answers Table

Table name: `answers`

| Field name                    | Description     |
|-------------------------------|-----------------|
| question_id : string          | The ID of the question this is an answer to. |
| answer_id : string            | Unique ID for the contributed answer. |
| worker_nonce : string         | A unique ID for the worker contributing this answer. |
| answer : string               | A JSON representation for the crowdworkers answer to the question |
| validity : number             | A float value between 0 (totally wrong) and 1 (perfect) representing how correct this answer is known to be. If this question's type is `train` then this is field is NULL. |
| timestamp : timestamp         | When the question was submitted |
| client_job_key : string       | An id for the client job that this answer is part of |

### API

Client interactions with Jobs and Questions:

 * GET `client_jobs/:client_job_key` If the `:client_job_key` exists, then returns the corresponding `client_job` entry.
 * GET `client_jobs/:client_job_key/training_questions` returns a JSON object with all the training questions for the specified job.
 * GET `client_jobs/:client_job_key/to_answer_questions` returns a JSON object with all the questions for crowdworkers to answer.

Client interactions with Answers:

 * PUT `client_jobs/:client_job_key/questions/:question_id/answers/:worker_nonce` If `:client_job_key` exists, and `:question_id` is a question from the client job's question group, then add an answer to that question for the associated worker nonce according to the JSON body of the PUT request.
 * GET `client_jobs/:client_job_key/questions/:question_id/answers` If `:client_job_key` exists, and `:question_id` is a question from the client job's question group, returns all answers to the question id.
 * GET `client_jobs/:client_job_key/answers` If `:client_job_key` exists, get all answers for this job.

Client interactions with Workers:

 * GET `client_jobs/:client_job_key/workers/:worker_nonce` If `:client_job_key` exists, and then returns a JSON list of answers submitted with field worker_nonce as `:worker_nonce`.
 * GET `client_jobs/:client_job_key/workers/:worker_nonce/quality_summary` If `:client_job_key` exists, and then returns a JSON object with details about the quality of the worker associated with `:worker_nonce`. Initially this is just `{ answer_count: number, quality: number }` where `answer_count` is the number of answers the worker has contributed, and `quality` is the average quality (as computed up with some small noise/abstraction so client's cannot easily infer correct answers).

Admin job management:

 * POST `active_jobs/:client_job_key` [Admin only]. Creates or updates a client job from the JSON body of the post.
 * GET `active_jobs` [Admin only]. Get the set of active jobs.
 * GET `active_jobs/:client_job_key/test_questions` [Admin only]. get the set of test questions for the job `:client_job_key`.
 * GET `inactive_jobs` [Admin only]. Get the set of jobs that are no longer active.
 * DELETE `active_jobs/:client_job_key` [Admin only]. Removes the client job.

Admin question management:

 * POST `questions`  [Admin only]. create a set of questions from the specified JSON.
 * DELETE `question_groups/:question_group_id`  [Admin only]. Removes all questions with `question_group_id` as `:question_group_id`.
 * DELETE `questions`  [Admin only]. post body is a JSON list of quetion ids, removes all those question ids.
 * DELETE `questions/:question_id`  [Admin only]. Removes the question with id `:question_id`.



## About this code

This repository contains example code to help experimentation with the Perspective API; it is not an official Google product.
