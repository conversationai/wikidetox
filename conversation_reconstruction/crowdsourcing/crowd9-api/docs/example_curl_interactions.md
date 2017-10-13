# Example CURL commands to interact with a Conversation AI crowdsource service

The following examples assuming you have the admin auth key from the
`build/config/server_config.json` in the bash environment variable
`ADMIN_AUTH_KEY`. It also assumes your are running the service locally.
e.g. you have run:

```
export ADMIN_AUTH_KEY="Your admin key from build/config/server_config.json"
export SERVER="${SERVER}"
```

### [Admin] Setup a small test job.

List the active jobs; initially returns empty list.

```
curl -H "x-admin-auth-key: ${ADMIN_AUTH_KEY}" \
     ${SERVER}/active_jobs
```

Add a new job

```
curl -H "x-admin-auth-key: ${ADMIN_AUTH_KEY}" \
     -H "Content-Type: application/json" -X POST -d '{
  "title":"some job title this",
  "description":"a beautiful soliloquy of a description this",
  "question_group_id":"foo1",
  "status":"setup",
  "answers_per_question":3,
  "answer_schema": "{"comments":{"stringInput":{}},"toxic":{"validEnumValues":["ok","unsure","toxic"]},"threat":{"validEnumValues":["ok","unsure","toxic"]},"insult":{"validEnumValues":["ok","unsure","toxic"]},"identityHate":{"validEnumValues":["ok","unsure","toxic"]},"obscene":{"validEnumValues":["ok","unsure","toxic"]}}"
  }' ${SERVER}/active_jobs/job1_for_foo1
```

You may now list the jobs again to see the one you just added.

```
curl -H "x-admin-auth-key: ${ADMIN_AUTH_KEY}" \
     ${SERVER}/active_jobs
```

Look at details of a particular job:

```
curl ${SERVER}/client_jobs/job1_for_foo1
```

Add 3 questions (1 training, 1 test and 1 toanswer)

```
curl -H "x-admin-auth-key: ${ADMIN_AUTH_KEY}" \
     -H "Content-Type: application/json" -X POST -d '[
  {
    "question_id": "q1",
    "question_group_id":"foo1",
    "question":"{\"string\":\"Is this a toxic comment?\"}",
    "accepted_answers": "{ \"toxicity\": { \"enumScores\": { \"ok\": 0, \"unsure\": -1, \"toxic\": -1 } } }",
    "type": "training"
  },
  {
    "question_id": "q2",
    "question_group_id":"foo1",
    "question":"{\"string\":\"Is this a shitty toxic comment?\"}",
    "accepted_answers": "{ \"toxicity\": { \"enumScores\": { \"ok\": -1, \"unsure\": 0, \"toxic\": 0 } } }",
    "type": "test"
  },
  {
    "question_id": "q3",
    "question_group_id":"foo1",
    "question":"{\"string\":\"Is this a toxic really comment?\"}",
    "accepted_answers": null,
    "type": "toanswer"
  },
  {
    "question_id": "q4",
    "question_group_id":"foo1",
    "question":"{\"string\":\"Is this a toxic really comment?\"}",
    "accepted_answers": null,
    "type": "toanswer"
  },
  {
    "question_id": "q4",
    "question_group_id":"foo2",
    "question":"{\"string\":\"foo2! q4?\"}",
    "accepted_answers": null,
    "type": "toanswer"
  },
  {
    "question_id": "q5",
    "question_group_id":"foo2",
    "question":"{\"string\":\"foo2! q5?\"}",
    "accepted_answers": null,
    "type": "toanswer"
  },
  {
    "question_id": "q6",
    "question_group_id":"foo2",
    "question":"{\"string\":\"foo2! q6?\"}",
    "accepted_answers": null,
    "type": "toanswer"
  }
  ]' ${SERVER}/questions
```

Create a second job:

```
curl -H "x-admin-auth-key: ${ADMIN_AUTH_KEY}" \
     -H "Content-Type: application/json" -X POST -d '{
  "title":"some job title this",
  "description":"a beautiful soliloquy of a description this",
  "question_group_id":"foo2",
  "status":"setup",
  "answers_per_question":3 }' ${SERVER}/active_jobs/job2_for_foo2
```

Now see that there are two jobs in the list:

```
curl -H "x-admin-auth-key: ${ADMIN_AUTH_KEY}" -X GET \
     ${SERVER}/active_jobs
```

See the questions for question group id `foo2`:

```
curl -H "x-admin-auth-key: ${ADMIN_AUTH_KEY}" -X GET \
     ${SERVER}/question_groups/foo2
```

Delete question from question with id `q6` and group `foo2`, then look at set of questions again:

```
curl -H "x-admin-auth-key: ${ADMIN_AUTH_KEY}" -X DELETE \
  ${SERVER}/questions/foo2/q6
curl -H "x-admin-auth-key: ${ADMIN_AUTH_KEY}" -X GET \
     ${SERVER}/question_groups/foo2
```

See the list of all question groups:

```
curl -H "x-admin-auth-key: ${ADMIN_AUTH_KEY}" -X GET \
     ${SERVER}/question_groups
```

You can also look at the questions to answer as if you are a client:

```
curl ${SERVER}/client_jobs/job2_for_foo2/to_answer_questions
```

Now delete the second job (`job2_for_foo2`):

```
curl -H "x-admin-auth-key: ${ADMIN_AUTH_KEY}" -X DELETE \
     ${SERVER}/active_jobs/job2_for_foo2
```

Observe it has been deleted by listing jobs again:

```
curl -H "x-admin-auth-key: ${ADMIN_AUTH_KEY}" -X GET \
     ${SERVER}/active_jobs
```

### Example client interactions:

Get job details:

```
curl ${SERVER}/client_jobs/job1_for_foo1
```

Get the training questions, and also the questions to be answerd by crowd-workers.

```
curl ${SERVER}/client_jobs/job1_for_foo1/training_questions
curl ${SERVER}/client_jobs/job1_for_foo1/to_answer_questions
```

Submit some answers from crowd-workers:

```
# Example answers with answer_id specified.
curl -H "Content-Type: application/json" -X POST -d \
  '{ "answer_id": "1", "answer": "{\"toxicity\": { \"enumAnswer\": \"ok\"} }" }' \
  ${SERVER}/client_jobs/job1_for_foo1/questions/q1/answers/user_fuzbar1
curl -H "Content-Type: application/json" -X POST -d \
  '{ "answer_id": "2", "answer": "{\"toxicity\": { \"enumAnswer\": \"unsure\"} }" }' \
  ${SERVER}/client_jobs/job1_for_foo1/questions/q1/answers/user_fuzbar1

curl -H "Content-Type: application/json" -X POST -d \
  '{ "answer": "{\"toxicity\": { \"enumAnswer\": \"toxic\"} }" }' \
  ${SERVER}/client_jobs/job1_for_foo1/questions/q1/answers/user_fuzbar2

curl -H "Content-Type: application/json" -X POST -d \
  '{ "answer": "{\"toxicity\": { \"enumAnswer\": \"toxic\"} }" }' \
  ${SERVER}/client_jobs/job1_for_foo1/questions/q2/answers/user_fuzbar1
curl -H "Content-Type: application/json" -X POST -d \
  '{ "answer": "{\"toxicity\": { \"enumAnswer\": \"unsure\"} }" }' \
  ${SERVER}/client_jobs/job1_for_foo1/questions/q2/answers/user_fuzbar2

curl -H "Content-Type: application/json" -X POST -d \
  '{ "answer": "{\"toxicity\": { \"enumAnswer\": \"ok\"} }" }' \
  ${SERVER}/client_jobs/job1_for_foo1/questions/q3/answers/user_fuzbar1
curl -H "Content-Type: application/json" -X POST -d \
  '{ "answer": "{\"toxicity\": { \"enumAnswer\": \"ok\"} }" }' \
  ${SERVER}/client_jobs/job1_for_foo1/questions/q3/answers/user_fuzbar2
```

Look at the questions that still need more answers:

```
curl -H "Content-Type: application/json" -X GET \
  ${SERVER}/client_jobs/job1_for_foo1/next10_unanswered_questions
```

Look at the questions that have enough answers:

```
curl -H "Content-Type: application/json" -X GET \
  ${SERVER}/client_jobs/job1_for_foo1/answered_questions
```

Look at the answers by workers:

```
curl -H "Content-Type: application/json" -X GET \
  ${SERVER}/client_jobs/job1_for_foo1/workers/user_fuzbar1
curl -H "Content-Type: application/json" -X GET \
  ${SERVER}/client_jobs/job1_for_foo1/workers/user_fuzbar2
```

Look at the workers' quality summary (for a given job, only on training questions):

```
curl -H "Content-Type: application/json" -X GET \
  ${SERVER}/client_jobs/job1_for_foo1/workers/user_fuzbar2/quality_summary
```

Look at all answers to the job:

```
curl -H "Content-Type: application/json" -X GET \
  ${SERVER}/client_jobs/job1_for_foo1/answers
```

Look at overall quality on secret questions:

```
curl -H "Content-Type: application/json" -X GET \
  ${SERVER}/client_jobs/job1_for_foo1/quality_summary
```

Look at the answers by question id:

```
curl -H "Content-Type: application/json" -X GET \
  ${SERVER}/client_jobs/job1_for_foo1/questions/q1/answers
curl -H "Content-Type: application/json" -X GET \
  ${SERVER}/client_jobs/job1_for_foo1/questions/q2/answers
curl -H "Content-Type: application/json" -X GET \
  ${SERVER}/client_jobs/job1_for_foo1/questions/q3/answers
```


### More example Admin Actions (after the client ones)

Get the list of scored answers:

```
curl -H "x-admin-auth-key: ${ADMIN_AUTH_KEY}" \
     ${SERVER}/scored_answers
```