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
import * as express from 'express';

import * as db_types from './db_types';
import * as crowdsourcedb from './crowdsourcedb';
import * as config from './config';
import * as httpcodes from './http-status-codes';

function requestFailsAuth(serverConfig: config.Config, req : express.Request) {
  return !req.headers['x-admin-auth-key'] ||
         req.headers['x-admin-auth-key'] === '' ||
         serverConfig.adminKey === '' ||
         req.headers['x-admin-auth-key'] !== serverConfig.adminKey;
}

// TODO(ldixon): consider using passport auth
// for google cloud project.
export function setup(app : express.Express,
                      // Server config used for adminKey.
                      serverConfig: config.Config,
                      crowdsourcedb: crowdsourcedb.CrowdsourceDB) {

  // If the `:client_job_key` exists, then returns the corresponding `client_job` entry.
  app.get('/client_jobs/:client_job_key', async (req, res) => {
    let clientJobRow : db_types.ClientJobRow;
    try {
      clientJobRow = await crowdsourcedb.getClientJob(req.params.client_job_key);
      res.status(httpcodes.OK).send(JSON.stringify(clientJobRow, null, 2));
    } catch(e) {
      console.error(`*** Failed: `, e);
      res.status(httpcodes.INTERNAL_SERVER_ERROR).send(JSON.stringify({ error: e.message }));
    }
  });

  // If the `:client_job_key` exists, returns a JSON object with all the training
  // questions for the specified job.
  app.get('/client_jobs/:client_job_key/training_questions', async (req, res) => {
    let questionToAnswer : crowdsourcedb.QuestionToAnswer[];
    try {
      questionToAnswer = await crowdsourcedb.getClientJobQuestions(req.params.client_job_key, true);
      res.status(httpcodes.OK).send(JSON.stringify(questionToAnswer, null, 2));
    } catch(e) {
      console.error(`*** Failed: `, e);
      res.status(httpcodes.INTERNAL_SERVER_ERROR).send(JSON.stringify({ error: e.message }));
    }
  });

  // If the `:client_job_key` exists, returns a JSON object with all the questions
  // for crowdworkers to answer.
  app.get('/client_jobs/:client_job_key/to_answer_questions', async (req, res) => {
    let questionToAnswer : crowdsourcedb.QuestionToAnswer[];
    try {
      questionToAnswer = await crowdsourcedb.getClientJobQuestions(req.params.client_job_key, false);
      res.status(httpcodes.OK).send(JSON.stringify(questionToAnswer, null, 2));
    } catch(e) {
      console.error(`*** Failed: `, e);
      res.status(httpcodes.INTERNAL_SERVER_ERROR).send(JSON.stringify({ error: e.message }));
    }
  });

  // If the `:client_job_key` exists, returns a JSON object with 10 questions
  // that still need answers.
  app.get('/client_jobs/:client_job_key/next10_unanswered_questions', async (req, res) => {
    let questionToAnswer : crowdsourcedb.QuestionToAnswer[];
    try {
      questionToAnswer = await crowdsourcedb.getClientJobNextOpenQuestions(req.params.client_job_key, 10);
      // TODO(ldixon): fix lying about type.
      res.status(httpcodes.OK).send(JSON.stringify(questionToAnswer, null, 2));
    } catch(e) {
      console.error(`*** Failed: `, e);
      res.status(httpcodes.INTERNAL_SERVER_ERROR).send(JSON.stringify({ error: e.message }));
    }
  });

  // If the `:client_job_key` exists, returns a JSON object with all questions
  // that now have enough answers.
  app.get('/client_jobs/:client_job_key/answered_questions', async (req, res) => {
    let questionToAnswer : crowdsourcedb.QuestionToAnswer[];
    try {
      questionToAnswer = await crowdsourcedb.getClientJobClosedQuestions(req.params.client_job_key);
      // TODO(ldixon): fix lying about type.
      res.status(httpcodes.OK).send(JSON.stringify(questionToAnswer, null, 2));
    } catch(e) {
      console.error(`*** Failed: `, e);
      res.status(httpcodes.INTERNAL_SERVER_ERROR).send(JSON.stringify({ error: e.message }));
    }
  });




  // If `:client_job_key` exists, and `:question_id` is a question from the
  // client job's question group, then add an answer to that question for the
  // associated worker nonce according to the JSON body of the POST request.
  //
  // TODO(ldixon): better error handling. e.g. each user should only be able to
  // submit one answer.
  app.post('/client_jobs/:client_job_key/questions/:question_id/answers/:worker_nonce',
      async (req, res) => {
    if(!req.body) {
      res.status(httpcodes.BAD_REQUEST).send(JSON.stringify({ error: 'no body' }));
      return;
    }
    let answerToQuestion : crowdsourcedb.AnswerToQuestion = req.body;
    answerToQuestion.client_job_key = req.params.client_job_key;
    answerToQuestion.question_id = req.params.question_id;
    answerToQuestion.worker_nonce = req.params.worker_nonce;
    if (!answerToQuestion.answer_id) {
      answerToQuestion.answer_id = null;
    }
    try {
      await crowdsourcedb.addAnswer(answerToQuestion);
      console.log('Answer added.');
      res.status(httpcodes.OK).send(JSON.stringify({ result: 'Answer added' }));
    } catch(e) {
      console.error('Error: Cannot add answer: ', e);
      res.status(httpcodes.INTERNAL_SERVER_ERROR).send(JSON.stringify({ error: e.message }));
      return;
    }
  });

  // Get the answers submitted by worker :worker_nonce in job :client_job_key.
  app.get('/client_jobs/:client_job_key/workers/:worker_nonce',
      async (req, res) => {
    try {
      let answers = await crowdsourcedb.getWorkerAnswers(
        req.params.client_job_key, req.params.worker_nonce);
      res.status(httpcodes.OK).send(JSON.stringify(answers, null, 2));
    } catch(e) {
      console.error('Error: Cannot get worker answers: ', e);
      res.status(httpcodes.INTERNAL_SERVER_ERROR).send(JSON.stringify({ error: e.message }));
      return;
    }
  });

  // If `:client_job_key` exists, and then returns a JSON object with details
  // about the quality of the worker associated with `:worker_nonce`. Initially
  // this is just `{ answer_count: number, quality: number }` where `answer_count`
  // is the number of answers the worker has contributed, and `quality` is the
  // average quality (as computed up with some small noise/abstraction so
  // client's cannot easily infer correct answers).
  app.get('/client_jobs/:client_job_key/workers/:worker_nonce/quality_summary',
      async (req, res) => {
    try {
      let workerQuality = await crowdsourcedb.getWorkerQuality(
        req.params.client_job_key, req.params.worker_nonce);
      res.status(httpcodes.OK).send(JSON.stringify(workerQuality, null, 2));
    } catch(e) {
      console.error('Error: Cannot get worker answers: ', e);
      res.status(httpcodes.INTERNAL_SERVER_ERROR).send(JSON.stringify({ error: e.message }));
      return;
    }
  });

  // If `:client_job_key` exists, returns all answers to the job.
  // TODO(ldixon): consider using URL:
  //   client_jobs/:client_job_key/questions/*/answers
  app.get('/client_jobs/:client_job_key/answers',
      async (req, res) => {
    try {
      let answers = await crowdsourcedb.getJobAnswers(
        req.params.client_job_key);
      res.status(httpcodes.OK).send(JSON.stringify(answers, null, 2));
    } catch(e) {
      console.error('Error: Cannot get worker answers: ', e);
      res.status(httpcodes.INTERNAL_SERVER_ERROR).send(JSON.stringify({ error: e.message }));
      return;
    }
  });

  // If `:client_job_key` exists, and `:question_id` is a question from the
  // client job's question group, returns all answers to the question id.
  app.get('/client_jobs/:client_job_key/questions/:question_id/answers',
      async (req, res) => {
    try {
      let answers = await crowdsourcedb.getQuestionAnswers(
        req.params.client_job_key, req.params.question_id);
      res.status(httpcodes.OK).send(JSON.stringify(answers, null, 2));
    } catch(e) {
      console.error('Error: Cannot get worker answers: ', e);
      res.status(httpcodes.INTERNAL_SERVER_ERROR).send(JSON.stringify({ error: e.message }));
      return;
    }
  });

  // If `:client_job_key` exists, returns quality on hidden questions.
  // TODO(ldixon): consider using URL:
  //   client_jobs/:client_job_key/questions/*/answers
  app.get('/client_jobs/:client_job_key/quality_summary',
      async (_req, res) => {
    try {
      // let answers = await crowdsourcedb.getJobAnswers(
      //   req.params.client_job_key);
      res.status(httpcodes.NOT_IMPLEMENTED).send(JSON.stringify({ error: 'Not yet implemented.' }));
    } catch(e) {
      console.error('Error: Cannot get worker answers: ', e);
      res.status(httpcodes.INTERNAL_SERVER_ERROR).send(JSON.stringify({ error: e.message }));
      return;
    }
  });


  // Admin
  app.get('/active_jobs', async (req, res) => {
    if(requestFailsAuth(serverConfig, req)) {
      res.status(httpcodes.FORBIDDEN).send(JSON.stringify({ error: 'permission failure' }));
      return;
    }
    let clientJobRows : db_types.ClientJobRow[];
    try {
      clientJobRows = await crowdsourcedb.getAllClientJobs();
      res.status(httpcodes.OK).send(JSON.stringify(clientJobRows, null, 2));
    } catch(e) {
      console.error(`*** Failed: `, e);
      res.status(httpcodes.INTERNAL_SERVER_ERROR).send(JSON.stringify({ error: e.message }));
    }
  });

  app.post('/active_jobs/:client_job_key', async (req, res) => {
    if(requestFailsAuth(serverConfig, req)) {
      res.status(httpcodes.FORBIDDEN).send(JSON.stringify({ error: 'permission failure' }));
      return;
    }
    if(!req.body) {
      res.status(httpcodes.BAD_REQUEST).send(JSON.stringify({ error: 'no body' }));
      return;
    }

    let clientJobRow : db_types.ClientJobRow;
    try {
      console.log(JSON.stringify(req.body));
      clientJobRow = req.body;
      clientJobRow.client_job_key = req.params.client_job_key;
    } catch(e) {
      console.error(`Failed to parse body: ${req.body}`, e);
      res.status(httpcodes.BAD_REQUEST).send(JSON.stringify({ error: e.message }));
      return;
    }

    try {
      await crowdsourcedb.addClientJob(clientJobRow);
      console.log('New client job created!');
      res.status(httpcodes.OK).send(JSON.stringify({ result: 'New client job created' }));
    } catch(e) {
      console.error('Error: Cannot insert (maybe dup key): ', e);
      res.status(httpcodes.INTERNAL_SERVER_ERROR).send(JSON.stringify({ error: e.message }));
      return;
    }
  });

  // [Admin only]. create a set of questions from the specified JSON.
  // Body of the request should be a JSON in format crowdsourcedb.QuestionRow[]
  app.post('/questions', async (req, res) => {
    if(requestFailsAuth(serverConfig, req)) {
      res.status(httpcodes.FORBIDDEN).send(JSON.stringify({ error: 'permission failure' }));
      return;
    }
    if(!req.body) {
      res.status(httpcodes.BAD_REQUEST).send(JSON.stringify({ error: 'no body' }));
      return;
    }

    let questionRows : db_types.QuestionRow[] = req.body;
    console.log('number of entries: ' + req.body.length);

    try {
      // await crowdsourcedb.updateQuestions(questionRows);
      await crowdsourcedb.addQuestions(questionRows);
      console.log('Questions added.');
      res.status(httpcodes.OK).send(JSON.stringify({ result: 'Questions added.' }));
    } catch(e) {
      // TODO(ldixon): make error messages and codes consistent.
      console.error('Error: Cannot add questions: ', e);
      res.status(httpcodes.INTERNAL_SERVER_ERROR).send(JSON.stringify({ error: e.message }));
      return;
    }
  });

  // [Admin only]. create a set of questions from the specified JSON.
  // Body of the request should be a JSON in format crowdsourcedb.QuestionRow[]
  app.patch('/questions', async (req, res) => {
    if(requestFailsAuth(serverConfig, req)) {
      res.status(httpcodes.FORBIDDEN).send(JSON.stringify({ error: 'permission failure' }));
      return;
    }
    if(!req.body) {
      res.status(httpcodes.BAD_REQUEST).send(JSON.stringify({ error: 'no body' }));
      res.status(httpcodes.BAD_REQUEST).send(JSON.stringify({ error: 'no body' }));

      return;
    }

    let questionRows : db_types.QuestionRow[] = req.body;
    console.log('number of entries: ' + req.body.length);

    try {
      await crowdsourcedb.updateQuestions(questionRows);
      console.log('Questions updated.');
      res.status(httpcodes.OK).send('Questions updated.');
    } catch(e) {
      // TODO(ldixon): make error messages and codes consistent.
      console.error('Error: Cannot add questions: ', e);
      res.status(httpcodes.INTERNAL_SERVER_ERROR).send(JSON.stringify({ error: e.message }));
      return;
    }
  });

  // [Admin only]. Removes the client job.
  app.delete('/active_jobs/:client_job_key',
      async (req, res) => {
    if(requestFailsAuth(serverConfig, req)) {
      res.status(httpcodes.FORBIDDEN).send(JSON.stringify({ error: 'permission failure' }));
      return;
    }
    try {
      await crowdsourcedb.deleteClientJobs([req.params.client_job_key]);
      console.log('Job Deleted.');
      res.status(httpcodes.OK).send('Job Deleted.');
    } catch(e) {
      // TODO(ldixon): make error messages and codes consistent.
      console.error('Error: Cannot delete ClientJob: ', e);
      res.status(httpcodes.INTERNAL_SERVER_ERROR).send(JSON.stringify({ error: e.message }));
      return;
    }
  });


  // Admin
  app.get('/question_groups', async (req, res) => {
    if(requestFailsAuth(serverConfig, req)) {
      res.status(httpcodes.FORBIDDEN).send(JSON.stringify({ error: 'permission failure' }));
      return;
    }
    let questionGroupRows : crowdsourcedb.QuestionGroupRow[];
    try {
      questionGroupRows = await crowdsourcedb.getAllQuestionGroups();
      res.status(httpcodes.OK).send(JSON.stringify(questionGroupRows, null, 2));
    } catch(e) {
      console.error(`*** Failed: `, e);
      res.status(httpcodes.INTERNAL_SERVER_ERROR).send(JSON.stringify({ error: e.message }));
    }
  });

  // Admin
  app.get('/scored_answers', async (req, res) => {
    if(requestFailsAuth(serverConfig, req)) {
      res.status(httpcodes.FORBIDDEN).send(JSON.stringify({ error: 'permission failure' }));
      return;
    }
    let scoredAnswerRows : crowdsourcedb.ScoredAnswer[];
    try {
      scoredAnswerRows = await crowdsourcedb.getScoredAnswers();
      res.status(httpcodes.OK).send(JSON.stringify(scoredAnswerRows, null, 2));
    } catch(e) {
      console.error(`*** Failed: `, e);
      res.status(httpcodes.INTERNAL_SERVER_ERROR).send(JSON.stringify({ error: e.message }));
    }
  });

  // Admin
  app.get('/question_groups/:question_group_id', async (req, res) => {
    if(requestFailsAuth(serverConfig, req)) {
      res.status(httpcodes.FORBIDDEN).send(JSON.stringify({ error: 'permission failure' }));
      return;
    }
    let questionRows : db_types.QuestionRow[];
    try {
      questionRows = await crowdsourcedb.getQuestionGroupQuestions(req.params.question_group_id);
      res.status(httpcodes.OK).send(JSON.stringify(questionRows, null, 2));
    } catch(e) {
      console.error(`*** Failed: `, e);
      res.status(httpcodes.INTERNAL_SERVER_ERROR).send(JSON.stringify({ error: e.message }));
    }
  });

  // [Admin only]. Removes the question with id `:question_id`.
  app.delete('/questions/:question_group_id/:question_id',
      async (req, res) => {
    if(requestFailsAuth(serverConfig, req)) {
      res.status(httpcodes.FORBIDDEN).send(JSON.stringify({ error: 'permission failure' }));
      return;
    }
    try {
      await crowdsourcedb.deleteQuestions(
        [{question_group_id: req.params.question_group_id,
          question_id: req.params.question_id}]);
      console.log('Question deleted.');
      res.status(httpcodes.OK).send(JSON.stringify({ result: 'Question deleted.' }));
    } catch(e) {
      // TODO(ldixon): make error messages and codes consistent.
      console.error('Error: Cannot delete question: ', e);
      res.status(httpcodes.INTERNAL_SERVER_ERROR).send(JSON.stringify({ error: e.message }));
      return;
    }
  });

  // [Admin only]. Updates a question's fields.
  app.patch('/questions/:question_group_id/:question_id', async (req, res) => {
    if(requestFailsAuth(serverConfig, req)) {
      res.status(httpcodes.FORBIDDEN).send(JSON.stringify({ error: 'permission failure' }));
      return;
    }
    if(!req.body) {
      res.status(httpcodes.BAD_REQUEST).send(JSON.stringify({ error: 'no body' }));
      return;
    }
    let questionRow : db_types.QuestionRow = req.body;
    questionRow.question_group_id = req.params.question_group_id;
    questionRow.question_id = req.params.question_id;
    try {
      await crowdsourcedb.updateQuestions([questionRow]);
      console.log('Question patched.');
      res.status(httpcodes.OK).send(JSON.stringify({ result: 'Question patched.' }));
    } catch(e) {
      // TODO(ldixon): make error messages and codes consistent.
      console.error('Error: Cannot delete question: ', e);
      res.status(httpcodes.INTERNAL_SERVER_ERROR).send(JSON.stringify({ error: e.message }));
      return;
    }
  });

}