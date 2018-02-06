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

import * as config from './config';
import * as crowdsourcedb from './cs_db';
import * as db_types from './db_types';
import * as httpcodes from './http-status-codes';

function requestFailsAuth(serverConfig: config.Config, req: express.Request) {
  return !req.headers['x-admin-auth-key'] ||
      req.headers['x-admin-auth-key'] === '' || serverConfig.adminKey === '' ||
      req.headers['x-admin-auth-key'] !== serverConfig.adminKey;
}

// TODO(ldixon): consider using passport auth
// for google cloud project.
export function setup(
    app: express.Express,
    // Server config used for adminKey.
    serverConfig: config.Config, crowdsourcedb: crowdsourcedb.CrowdsourceDB) {
  // If `:client_job_key` exists, returns quality on hidden test questions.
  app.get('/active_jobs/:client_job_key/test_answers', async (req, res) => {
    if (requestFailsAuth(serverConfig, req)) {
      res.status(httpcodes.FORBIDDEN).send(JSON.stringify({
        error: 'permission failure'
      }));
      return;
    }
    try {
      let test_answers =
          await crowdsourcedb.getJobTestAnswers(req.params.client_job_key);
      res.status(httpcodes.OK).send(test_answers);
    } catch (e) {
      console.error('Error: Cannot get worker answers: ', e);
      res.status(httpcodes.INTERNAL_SERVER_ERROR).send(JSON.stringify({
        error: e.message
      }));
      return;
    }
  });

  // Admin
  app.get('/active_jobs', async (req, res) => {
    if (requestFailsAuth(serverConfig, req)) {
      res.status(httpcodes.FORBIDDEN).send(JSON.stringify({
        error: 'permission failure'
      }));
      return;
    }
    let clientJobRows: db_types.ClientJobRow[];
    try {
      clientJobRows = await crowdsourcedb.getAllClientJobs();
      res.status(httpcodes.OK).send(JSON.stringify(clientJobRows, null, 2));
    } catch (e) {
      console.error(`*** Failed: `, e);
      res.status(httpcodes.INTERNAL_SERVER_ERROR).send(JSON.stringify({
        error: e.message
      }));
    }
  });

  app.post('/active_jobs/:client_job_key', async (req, res) => {
    if (requestFailsAuth(serverConfig, req)) {
      res.status(httpcodes.FORBIDDEN).send(JSON.stringify({
        error: 'permission failure'
      }));
      return;
    }
    if (!req.body) {
      res.status(httpcodes.BAD_REQUEST).send(JSON.stringify({
        error: 'no body'
      }));
      return;
    }

    let clientJobRow: db_types.ClientJobRow;
    try {
      console.log(JSON.stringify(req.body));
      clientJobRow = req.body;
      clientJobRow.client_job_key = req.params.client_job_key;
    } catch (e) {
      console.error(`Failed to parse body: ${req.body}`, e);
      res.status(httpcodes.BAD_REQUEST).send(JSON.stringify({
        error: e.message
      }));
      return;
    }

    try {
      await crowdsourcedb.addClientJob(clientJobRow);
      console.log('New client job created!');
      res.status(httpcodes.OK).send(JSON.stringify({
        result: 'New client job created'
      }));
    } catch (e) {
      console.error('Error: Cannot insert: ', e);
      res.status(httpcodes.INTERNAL_SERVER_ERROR).send(JSON.stringify({
        error: e.message
      }));
      return;
    }
  });

  app.patch('/active_jobs/:client_job_key', async (req, res) => {
    if (requestFailsAuth(serverConfig, req)) {
      res.status(httpcodes.FORBIDDEN).send(JSON.stringify({
        error: 'permission failure'
      }));
      return;
    }
    if (!req.body) {
      res.status(httpcodes.BAD_REQUEST).send(JSON.stringify({
        error: 'no body'
      }));
      return;
    }

    let clientJobRow: db_types.ClientJobRow;
    try {
      console.log(JSON.stringify(req.body));
      clientJobRow = req.body;
      clientJobRow.client_job_key = req.params.client_job_key;
    } catch (e) {
      console.error(`Failed to parse body: ${req.body}`, e);
      res.status(httpcodes.BAD_REQUEST).send(JSON.stringify({
        error: e.message
      }));
      return;
    }

    try {
      await crowdsourcedb.updateClientJob(clientJobRow);
      console.log('client updated!');
      res.status(httpcodes.OK).send(JSON.stringify({
        result: 'Client job updated'
      }));
    } catch (e) {
      console.error('Error: Cannot update: ', e);
      res.status(httpcodes.INTERNAL_SERVER_ERROR).send(JSON.stringify({
        error: e.message
      }));
      return;
    }
  });

  // [Admin only]. create a set of questions from the specified JSON.
  // Body of the request should be a JSON in format crowdsourcedb.QuestionRow[]
  app.post('/questions', async (req, res) => {
    if (requestFailsAuth(serverConfig, req)) {
      res.status(httpcodes.FORBIDDEN).send(JSON.stringify({
        error: 'permission failure'
      }));
      return;
    }
    if (!req.body) {
      res.status(httpcodes.BAD_REQUEST).send(JSON.stringify({
        error: 'no body'
      }));
      return;
    }

    let questionRows: db_types.QuestionRow[] = req.body;
    console.log('number of entries: ' + req.body.length);

    try {
      // await crowdsourcedb.updateQuestions(questionRows);
      await crowdsourcedb.addQuestions(questionRows);
      console.log('Questions added.');
      res.status(httpcodes.OK).send(JSON.stringify({
        result: 'Questions added.'
      }));
    } catch (e) {
      // TODO(ldixon): make error messages and codes consistent.
      console.error('Error: Cannot add questions: ', e);
      res.status(httpcodes.INTERNAL_SERVER_ERROR).send(JSON.stringify({
        error: e.message
      }));
      return;
    }
  });

  // [Admin only]. create a set of questions from the specified JSON.
  // Body of the request should be a JSON in format crowdsourcedb.QuestionRow[]
  app.patch('/questions', async (req, res) => {
    if (requestFailsAuth(serverConfig, req)) {
      res.status(httpcodes.FORBIDDEN).send(JSON.stringify({
        error: 'permission failure'
      }));
      return;
    }
    if (!req.body) {
      res.status(httpcodes.BAD_REQUEST).send(JSON.stringify({
        error: 'no body'
      }));
      return;
    }

    let questionRows: db_types.QuestionRow[] = req.body;
    console.log('number of entries: ' + req.body.length);

    try {
      await crowdsourcedb.updateQuestions(questionRows);
      console.log('Questions updated.');
      res.status(httpcodes.OK).send('Questions updated.');
    } catch (e) {
      // TODO(ldixon): make error messages and codes consistent.
      console.error('Error: Cannot add questions: ', e);
      res.status(httpcodes.INTERNAL_SERVER_ERROR).send(JSON.stringify({
        error: e.message
      }));
      return;
    }
  });

  // [Admin only]. Removes the client job.
  app.delete('/active_jobs/:client_job_key', async (req, res) => {
    if (requestFailsAuth(serverConfig, req)) {
      res.status(httpcodes.FORBIDDEN).send(JSON.stringify({
        error: 'permission failure'
      }));
      return;
    }
    try {
      await crowdsourcedb.deleteClientJobs([req.params.client_job_key]);
      console.log('Job Deleted.');
      res.status(httpcodes.OK).send('Job Deleted.');
    } catch (e) {
      // TODO(ldixon): make error messages and codes consistent.
      console.error('Error: Cannot delete ClientJob: ', e);
      res.status(httpcodes.INTERNAL_SERVER_ERROR).send(JSON.stringify({
        error: e.message
      }));
      return;
    }
  });


  // Admin
  app.get('/question_groups', async (req, res) => {
    if (requestFailsAuth(serverConfig, req)) {
      res.status(httpcodes.FORBIDDEN).send(JSON.stringify({
        error: 'permission failure'
      }));
      return;
    }
    let questionGroupRows: crowdsourcedb.QuestionGroupRow[];
    try {
      questionGroupRows = await crowdsourcedb.getAllQuestionGroups();
      res.status(httpcodes.OK).send(JSON.stringify(questionGroupRows, null, 2));
    } catch (e) {
      console.error(`*** Failed: `, e);
      res.status(httpcodes.INTERNAL_SERVER_ERROR).send(JSON.stringify({
        error: e.message
      }));
    }
  });

  // Admin
  app.get('/active_jobs/:client_job_key/scored_answers', async (req, res) => {
    if (requestFailsAuth(serverConfig, req)) {
      res.status(httpcodes.FORBIDDEN).send(JSON.stringify({
        error: 'permission failure'
      }));
      return;
    }
    let scoredAnswerRows: crowdsourcedb.ScoredAnswer[];
    try {
      scoredAnswerRows =
          await crowdsourcedb.getScoredAnswers(req.params.client_job_key);
      res.status(httpcodes.OK).send(JSON.stringify(scoredAnswerRows, null, 2));
    } catch (e) {
      console.error(`*** Failed: `, e);
      res.status(httpcodes.INTERNAL_SERVER_ERROR).send(JSON.stringify({
        error: e.message
      }));
    }
  });

  // Admin
  app.get('/question_groups/:question_group_id', async (req, res) => {
    if (requestFailsAuth(serverConfig, req)) {
      res.status(httpcodes.FORBIDDEN).send(JSON.stringify({
        error: 'permission failure'
      }));
      return;
    }
    let questionRows: db_types.QuestionRow[];
    try {
      questionRows = await crowdsourcedb.getQuestionGroupQuestions(
          req.params.question_group_id);
      res.status(httpcodes.OK).send(JSON.stringify(questionRows, null, 2));
    } catch (e) {
      console.error(`*** Failed: `, e);
      res.status(httpcodes.INTERNAL_SERVER_ERROR).send(JSON.stringify({
        error: e.message
      }));
    }
  });

  // [Admin only]. Get full details about a question.
  app.get('/questions/:question_group_id/:question_id', async (req, res) => {
    if (requestFailsAuth(serverConfig, req)) {
      res.status(httpcodes.FORBIDDEN).send(JSON.stringify({
        error: 'permission failure'
      }));
      return;
    }
    try {
      let questionRow = await crowdsourcedb.getQuestion(
          req.params.question_group_id, req.params.question_id);
      res.status(httpcodes.OK).send(JSON.stringify(questionRow));
    } catch (e) {
      // TODO(ldixon): make error messages and codes consistent.
      console.error('Error: Cannot get question: ', e);
      res.status(httpcodes.INTERNAL_SERVER_ERROR).send(JSON.stringify({
        error: e.message
      }));
      return;
    }
  });

  // [Admin only]. Removes the question with id `:question_id`.
  app.delete('/questions/:question_group_id/:question_id', async (req, res) => {
    if (requestFailsAuth(serverConfig, req)) {
      res.status(httpcodes.FORBIDDEN).send(JSON.stringify({
        error: 'permission failure'
      }));
      return;
    }
    try {
      await crowdsourcedb.deleteQuestions([{
        question_group_id: req.params.question_group_id,
        question_id: req.params.question_id
      }]);
      console.log('Question deleted.');
      res.status(httpcodes.OK).send(JSON.stringify({
        result: 'Question deleted.'
      }));
    } catch (e) {
      // TODO(ldixon): make error messages and codes consistent.
      console.error('Error: Cannot delete question: ', e);
      res.status(httpcodes.INTERNAL_SERVER_ERROR).send(JSON.stringify({
        error: e.message
      }));
      return;
    }
  });

  // [Admin only]. Updates a question's fields.
  app.patch('/questions/:question_group_id/:question_id', async (req, res) => {
    if (requestFailsAuth(serverConfig, req)) {
      res.status(httpcodes.FORBIDDEN).send(JSON.stringify({
        error: 'permission failure'
      }));
      return;
    }
    if (!req.body) {
      res.status(httpcodes.BAD_REQUEST).send(JSON.stringify({
        error: 'no body'
      }));
      return;
    }
    let questionRow: db_types.QuestionRow = req.body;
    questionRow.question_group_id = req.params.question_group_id;
    questionRow.question_id = req.params.question_id;
    try {
      await crowdsourcedb.updateQuestions([questionRow]);
      console.log('Question patched.');
      res.status(httpcodes.OK).send(JSON.stringify({
        result: 'Question patched.'
      }));
    } catch (e) {
      // TODO(ldixon): make error messages and codes consistent.
      console.error('Error: Cannot delete question: ', e);
      res.status(httpcodes.INTERNAL_SERVER_ERROR).send(JSON.stringify({
        error: e.message
      }));
      return;
    }
  });
}
