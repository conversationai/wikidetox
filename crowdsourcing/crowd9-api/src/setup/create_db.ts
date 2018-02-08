/*
Copyright 2017 Google Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

/*

This script creates the spanner database. It assumes that the cloud project and
spanner instance have been created.

This script is intended to be run locally; this means you will need application
default credentials need to be set. This can be done by downloading
credentials keyfile, and setting the `GOOGLE_APPLICATION_CREDENTIALS` variable.
This will need to be a "compute engine default service account credentials",
which you can create at:
https://pantheon.corp.google.com/apis/credentials/serviceaccountkey

```
export GOOGLE_APPLICATION_CREDENTIALS="tmp/path-to-keyfile.json"

node build/server/setup/create_db.js \
  --gcloud_project_id=wikidetox \
  --spanner_instance=crowdsource \
  --spanner_db_to_create=ptoxic
```

*/

import * as spanner from '@google-cloud/spanner';
import * as fs from 'fs';
import * as yargs from 'yargs';

interface Params {
  gcloud_project_id: string, spanner_instance: string,
      spanner_db_to_create: string
}

async function main(args: Params) {
  let spannerClient: spanner.Spanner;
  let spannerInstance: spanner.Instance;

  spannerClient = spanner({projectId: args.gcloud_project_id});
  spannerInstance = spannerClient.instance(args.spanner_instance);

  // Note: Cloud Spanner interprets Node.js numbers as FLOAT64s, so they
  // must be converted to strings before being inserted as INT64s
  const request = {
    schema: [
      // Table for jobs that a client can do.
      `CREATE TABLE ClientJobs (
        answers_per_question    INT64,
        client_job_key          STRING(1024),
        description             STRING(MAX),
        question_group_id       STRING(1024),
        answer_schema           STRING(MAX),
        title                   STRING(MAX),
        status                  STRING(1024),
      ) PRIMARY KEY (client_job_key)`,
      `CREATE INDEX ClientJobByQuestionGroupId ON ClientJobs(question_group_id)`,

      // TODO(ldixon): consider for security: separate accepted_answers into
      // training_answers and test_answers; help avoid leaking test_answers.
      // TODO(ldixon): Make accepted answers its own table, with a different
      // accepted answer per answer part. Avoid embedding JSON structure in
      // table values.
      `CREATE TABLE Questions (
        accepted_answers        STRING(MAX),
        question                STRING(MAX),
        question_group_id       STRING(1024),
        question_id             STRING(1024),
        type                    STRING(1024),
      ) PRIMARY KEY (question_group_id, question_id)`,
      `CREATE INDEX QuestionByGroupIdTypeAndId
        ON Questions(question_group_id, type, question_id)`,

      // Table that describes how an answer to a question, and what score it
      // will get. Only relevant for
      // `test` questions and `training` questions. `toanswer` questions don't
      // have an `accepted_answers` field.
      `CREATE TABLE QuestionScorings (
          question_group_id       STRING(1024),
          question_id             STRING(1024),
          answer_part_id          STRING(1024),
          answer                  STRING(1024),
          answer_score            FLOAT64,
        ) PRIMARY KEY (question_group_id, question_id)`,

      // Table for answers.
      `CREATE TABLE Answers (
        answer                  STRING(MAX),
        answer_id               STRING(1024),
        answer_part_id          STRING(1024),
        client_job_key          STRING(1024),
        question_group_id       STRING(1024),
        question_id             STRING(1024),
        timestamp               TIMESTAMP,
        answer_score            FLOAT64,
        worker_nonce            STRING(1024),
      ) PRIMARY KEY (client_job_key, question_group_id, question_id, worker_nonce, answer_id)`,
      `CREATE INDEX AnswerByClientJobToTimestamp
          ON Answers(client_job_key, question_group_id, timestamp DESC)`,
      `CREATE INDEX AnswerByTimestamp ON Answers(timestamp DESC)`,
      `CREATE INDEX AnswerByWorkerNonce ON Answers(client_job_key, worker_nonce)`,
    ]
  };

  console.log(`Creating DB... ${args.spanner_db_to_create}, ${
      JSON.stringify(request, null, 2)}`);

  // Creates a database
  return spannerInstance.createDatabase(args.spanner_db_to_create, request)
      .then((results) => {
        const database = results[0];
        const operation = results[1];

        console.log(`Waiting for operation on ${database.id} to complete...`);
        return operation.promise();
      })
      .then(() => {
        console.log(`Created database ${
            args.spanner_db_to_create} on instance ${args.spanner_instance}.`);
      })
      .catch((e) => {
        console.error(`*** Failed: `, e);
      });
}

let args =
    yargs
        .option(
            'gcloud_project_id',
            {alias: 'gcp', describe: 'Google Cloud Project Id'})
        .option(
            'spanner_instance', {alias: 'i', describe: 'Spanner instance name'})
        .option(
            'spanner_db_to_create',
            {alias: 's', describe: 'Spanner database name'})
        .default('update_only', false)
        .default('gcloud_project_id', 'wikidetox')
        .default('spanner_instance', 'crowdsource')
        .demandOption(
            ['spanner_db_to_create'],
            'Please provide at least --spanner_db_to_create.')
        .help()
        .argv;

main(args as any as Params)
    .then(() => {
      console.log('Success!');
    })
    .catch(e => {
      console.error('Failed: ', e);
    });
