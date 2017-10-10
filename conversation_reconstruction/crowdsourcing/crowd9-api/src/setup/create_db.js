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
This script initialises the DB.

node src/setup/create_db.js
*/

// [START create_database]
// Imports the Google Cloud client library
const Spanner = require('@google-cloud/spanner');

// Instantiates a client
const spanner = Spanner({
  projectId: 'wikidetox'
});

// Uncomment these lines to specify the instance and database to use
const instanceId = 'crowdsource';
const databaseId = 'testdb';

// Gets a reference to a Cloud Spanner instance
const instance = spanner.instance(instanceId);

// Note: Cloud Spanner interprets Node.js numbers as FLOAT64s, so they
// must be converted to strings before being inserted as INT64s
const request = {
  schema: [
    `CREATE TABLE ClientJobs (
      answers_per_question    INT64,
      client_job_key          STRING(1024),
      description             STRING(MAX),
      question_group_id       STRING(1024),
      title                   STRING(MAX),
      status                  STRING(1024),
    ) PRIMARY KEY (client_job_key)`,
    `CREATE INDEX ClientJobByQuestionGroupId ON ClientJobs(question_group_id)`,

    // TODO(ldixon): consider for security: separate accepted_answers into
    // training_answers and test_answers; help avoid leaking test_answers.
    `CREATE TABLE Questions (
      accepted_answers        STRING(MAX),
      question                STRING(MAX),
      question_group_id       STRING(1024),
      question_id             STRING(1024),
      type                    STRING(1024),
    ) PRIMARY KEY (question_group_id, question_id)`,
    `CREATE INDEX QuestionByGroupIdTypeAndId
       ON Questions(question_group_id, type, question_id)`,

    `CREATE TABLE Answers (
      answer                  STRING(MAX),
      answer_id               STRING(1024),
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

console.log(`Creating DB... ${databaseId}, ${request}`);

// Creates a database
instance.createDatabase(databaseId, request)
  .then((results) => {
    const database = results[0];
    const operation = results[1];

    console.log(`Waiting for operation on ${database.id} to complete...`);
    return operation.promise();
  })
  .then(() => {
    console.log(`Created database ${databaseId} on instance ${instanceId}.`);
  })
  .catch((e) => {
    console.error(`*** Failed: `, e);
  });