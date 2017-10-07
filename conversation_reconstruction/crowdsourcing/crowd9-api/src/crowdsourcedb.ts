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

// Class to wrap interactions with spanner DB and encapsulate basic
// logic for database.
import * as spanner from '@google-cloud/spanner';
import * as db_types from './db_types';
import * as questionaire from './questionaire';

export interface QuestionToAnswer {
  question: string;
  question_id: string;
}

export interface AnswerToQuestion {
  answer_id: string | null; // /^\w+$/
  answer: string; // JSON
  client_job_key: string; // /^\w+$/
  question_id: string; // /^\w+$/
  worker_nonce: string;
}

export interface QualitySummary {
  mean_score : string;
}

export interface ScoredAnswer {
  answer_id : string;
  question_id : string;
  accepted_answers : string;
  answer_score : number;
  answer : string;
}

export interface QuestionGroupRow {
  question_group_id : string;
  number_of_questions : number;
}

export class NoResultsError extends Error {}

export class ResultsError<T> extends Error {
  constructor(message:string, public results: T[][]) {
    super(message);
  }
}

interface SpannerOutputRow { [key:string] : string | number | null };

// Convert spanner's output row representation into a more natural JSON
// representation that we can easily have typescript schema for.
function parseSpannerOutputRow<T>(row: spanner.ResultRow) : T {
  let parsedRow : SpannerOutputRow = {};
  for(let entry of row) {
    // console.log(row);
    if(entry.value === null) {
      parsedRow[entry.name] = null;
    } else if(typeof(entry.value) === 'string') {
      parsedRow[entry.name] = entry.value;
    } else if(entry.value instanceof Date) {
      parsedRow[entry.name] = entry.value.toJSON();
    } else if(typeof(entry.value.value) === 'string') {
      // TODO(this isn't safe for big INTs: probably need to change schema to be INT32?)
      let parsedInt = parseInt(entry.value.value);
      if (parsedInt !== null && parsedInt !== undefined) {
        parsedRow[entry.name] = parsedInt;
      } else {
        console.warn('*** entry value type being treated as string: ' + entry.value.value);
        parsedRow[entry.name] = entry.value.value;
      }
    } else {
      console.error('*** entry value type being treated as int; type: ', typeof(entry.value));
      console.error('*** entry value type being treated as int; value: ', JSON.stringify(entry.value, null, 2));
      parsedRow[entry.name] = null;
    }
  }
  return parsedRow as any as T;
}

// TODO(ldixon): when/if sessions expire, we need to reconnet.
// See: https://cloud.google.com/spanner/docs/sessions#keep_an_idle_session_alive
// (Yes, we do try to keep it alive, but we should still fail and recover
// gracefully if connections drop).

// CrowdsourceDB takes responsibility for checking parameters won't
// result in SQL injection or other bad things.
export class CrowdsourceDB {
  // Public to support tests.
  public spanner: spanner.Spanner;
  public spannerInstance: spanner.Instance;
  public spannerDatabase: spanner.Database;
  // TODO(ldixon): consider a typed table wrapper that does the natural
  // and sensible JSON interpretatin for insert, update, and list-returning
  // queries, and single-element queries.
  public answerTable: spanner.Table; // <AnswerRow>;
  public questionTable: spanner.Table; // <QuestionRow>;
  public clientJobTable: spanner.Table; // <ClientJobRow>;

  constructor(public config : {cloudProjectId:string,
                               spannerInstanceId:string,
                               spannerDatabaseName:string} ) {
    // TODO(ldixon): check: should this be done per query? Does this setup a
    // connection under the hood which might timeout/break etc? Or is this just
    // setting vars?
    this.spanner = spanner({ projectId: config.cloudProjectId });
    this.spannerInstance = this.spanner.instance(config.spannerInstanceId);
    this.spannerDatabase = this.spannerInstance.database(config.spannerDatabaseName, { keepAlive: 5 });
    // Instantiate Spanner table objects
    this.answerTable = this.spannerDatabase.table('Answers');
    this.questionTable = this.spannerDatabase.table('Questions');
    this.clientJobTable = this.spannerDatabase.table('ClientJobs');
  }


  public async getClientJob(client_job_key:string) : Promise<db_types.ClientJobRow> {
    db_types.assertClientJobKey(client_job_key);

    const query : spanner.Query = {
      sql: `SELECT * FROM ClientJobs WHERE client_job_key="${client_job_key}"`
    };
    let results:spanner.QueryResult[] = await this.spannerDatabase.run(query);
    if(results.length === 0 || results[0].length === 0){
      throw new NoResultsError('getClientJob: Resulted in empty query response');
    }
    if(results[0].length !== 1){
      throw new ResultsError('Strangely resulted in not 1 row', results);
    }
    return parseSpannerOutputRow<db_types.ClientJobRow>(results[0][0]);
  }

  public deleteClientJobs(client_job_keys:string[]) : Promise<void> {
    return this.clientJobTable.deleteRows(client_job_keys);
  }

  public async getAllClientJobs() : Promise<db_types.ClientJobRow[]> {
    const query : spanner.Query = {
      sql: `SELECT * FROM ClientJobs`
    };
    let results:spanner.QueryResult[] = await this.spannerDatabase.run(query);
    if(results.length === 0){
      throw new NoResultsError('getAllClientJobs: Resulted in no response.');
    }
    let clientJobRows = results[0].map(row => parseSpannerOutputRow<db_types.ClientJobRow>(row));
    return clientJobRows;
  }

  // Get all the answers that have not yet been scored.
  public async getScoredAnswers() : Promise<ScoredAnswer[]> {
    const query : spanner.Query = {
      sql: `SELECT q.question_id, a.answer_id, q.accepted_answers, a.answer, a.answer_score
            FROM Answers as a
              JOIN Questions as q
              ON a.question_id = q.question_id
            WHERE (q.accepted_answers IS NOT NULL AND CHAR_LENGTH(q.accepted_answers) > 0)`
    };
    let results:spanner.QueryResult[] = await this.spannerDatabase.run(query);
    if(results.length === 0){
      throw new NoResultsError('Resulted in empty query response');
    }
    let scoredAnswerRows = results[0].map(
      row => parseSpannerOutputRow<ScoredAnswer>(row));
    return scoredAnswerRows;
  }

  public async getClientJobClosedQuestions(
      client_job_key:string) : Promise<QuestionToAnswer[]> {
    db_types.assertClientJobKey(client_job_key)
    const query : spanner.Query = {
      sql: `SELECT q.question_id, q.question, c.answers_per_question, COUNT(1) as answer_count
            FROM ClientJobs as c
              JOIN Questions as q
                ON c.question_group_id = q.question_group_id
              JOIN Answers as a
                ON a.question_id = q.question_id
            WHERE c.client_job_key = "${client_job_key}"
              AND q.type != "training"
            GROUP BY q.question_id, q.question, c.answers_per_question
            HAVING answer_count >= c.answers_per_question
            `
    };
    let results:spanner.QueryResult[] = await this.spannerDatabase.run(query);
    if(results.length === 0){
      throw new NoResultsError('Resulted in empty query response');
    }
    let questionRows = results[0].map(
      row => parseSpannerOutputRow<QuestionToAnswer>(row));
    return questionRows;
  }

  public async getClientJobNextOpenQuestions(
      client_job_key:string, limit:number) : Promise<QuestionToAnswer[]> {
    db_types.assertClientJobKey(client_job_key)
    const query : spanner.Query = {
      sql: `SELECT q.question_id, q.question, c.answers_per_question,
              COUNT(a.question_id) as answer_count
            FROM ClientJobs as c
              JOIN Questions as q
                ON c.question_group_id = q.question_group_id
              LEFT JOIN Answers as a
                ON a.question_id = q.question_id
            WHERE c.client_job_key = "${client_job_key}"
              AND q.type != "training"
            GROUP BY q.question_id, q.question, c.answers_per_question, a.question_id
            HAVING (answer_count < c.answers_per_question) OR (a.question_id IS NULL)
            LIMIT ${limit}
            `
    };
    let results:spanner.QueryResult[] = await this.spannerDatabase.run(query);
    if(results.length === 0){
      throw new NoResultsError('Resulted in empty query response');
    }
    let questionRows = results[0].map(
      row => parseSpannerOutputRow<QuestionToAnswer>(row));
    return questionRows;
  }


  public async getClientJobQuestions(
      client_job_key:string,
      training: boolean) : Promise<QuestionToAnswer[]> {
    db_types.assertClientJobKey(client_job_key)
    const query : spanner.Query = {
      sql: `SELECT q.question_id, q.question ${training ? ', q.accepted_answers' : ''}
            FROM ClientJobs as c
              JOIN Questions as q
                ON c.question_group_id = q.question_group_id
            WHERE c.client_job_key = "${client_job_key}"
              AND q.type ${training ? '' : '!'}= "training"`
    };
    let results:spanner.QueryResult[] = await this.spannerDatabase.run(query);
    if(results.length === 0){
      throw new NoResultsError('Resulted in empty query response');
    }
    let questionRows = results[0].map(
      row => parseSpannerOutputRow<QuestionToAnswer>(row));
    return questionRows;
  }

  public async getQuestion(question_id:string) : Promise<db_types.QuestionRow> {
    db_types.assertQuestionId(question_id)
    const query : spanner.Query = {
      sql: `SELECT * FROM Questions WHERE question_id="${question_id}"`
    };
    let results:spanner.QueryResult[] = await this.spannerDatabase.run(query);
    if(results.length === 0 || results[0].length === 0){
      throw new NoResultsError('getQuestion: Resulted in empty query response');
    }
    if(results[0].length !== 1){
      throw new ResultsError('Strangely resulted in not 1 row', results);
    }
    return parseSpannerOutputRow<db_types.QuestionRow>(results[0][0]);
  }

  public async getQuestionGroupQuestions(question_group_id:string)
      : Promise<db_types.QuestionRow[]> {
    db_types.assertQuestionGroupId(question_group_id);
    const query : spanner.Query = {
      sql: `SELECT * FROM Questions WHERE question_group_id="${question_group_id}"`
    };
    let results:spanner.QueryResult[] = await this.spannerDatabase.run(query);
    if(results.length === 0){
      throw new NoResultsError('getQuestion: Resulted in empty query response');
    }
    return results[0].map(r => parseSpannerOutputRow<db_types.QuestionRow>(r));
  }

  public deleteAnswers(answer_ids:string[]) : Promise<void> {
    return this.answerTable.deleteRows(answer_ids);
  }

  // TODO(ldixon): consider what to do with answers to this question? Delete them too I guess?
  public deleteQuestions(questionsToDelete: {question_group_id:string; question_id:string}[]) : Promise<void> {
    return this.questionTable.deleteRows(questionsToDelete.map(
      q => [q.question_group_id, q.question_id]));
  }

  public async addAnswer(answer:AnswerToQuestion) {
    let question : db_types.QuestionRow = await this.getQuestion(answer.question_id);
    db_types.assertClientJobKey(answer.client_job_key);
    let answer_score :number | null = null;
    if (question.accepted_answers) {
      answer_score = questionaire.answerScoreFromJson(question.accepted_answers, answer.answer);
    }

    // TODO(ldixon): don't allow multiple submission per user.
    let answerRow : db_types.AnswerRow = {
      answer: answer.answer,
      answer_id: answer.answer_id,
      client_job_key: answer.client_job_key,
      question_id: answer.question_id,
      question_group_id: question.question_group_id,
      answer_score: answer_score,
      worker_nonce: answer.worker_nonce,
      timestamp: new Date().toJSON()
    };
    return this.answerTable.insert([db_types.prepareAnswerSpannerInputRow(answerRow)]);
  }

  public async addClientJob(clientJob:db_types.ClientJobRow) {
    db_types.assertClientJobKey(clientJob.client_job_key);
    db_types.assertQuestionGroupId(clientJob.question_group_id);
    // TODO(ldixon): check answers_per_question & give nice error.
    // if(!regexp_strict_positive_number.test(client_job_row.answers_per_question)) {
    //   res.status(400).send('bad param: answers_per_question: ' +
    //       JSON.stringify(client_job_row.answers_per_question));
    //   return;
    // }
    return this.clientJobTable.insert([db_types.prepareClientJobSpannerInputRow(clientJob)]);
  }

  public async addQuestions(questions:db_types.QuestionRow[]) {

    // TODO: validate questions have valid ids.
    let spannerInputRows : spanner.InputRow[] =
      questions.map(q => {
        db_types.assertQuestionId(q.question_id);
        db_types.assertQuestionGroupId(q.question_group_id);
        return db_types.prepareQuestionSpannerInputRow(q);
      });
    return this.questionTable.insert(spannerInputRows);
  }

  public async getWorkerAnswers(client_job_key:string, worker_nonce:string)
      : Promise<db_types.AnswerRow[]> {
    db_types.assertClientJobKey(client_job_key);
    db_types.assertWorkerNonce(worker_nonce);
    const query : spanner.Query = {
      sql: `SELECT question_id, answer_id, timestamp, answer FROM Answers
            WHERE client_job_key="${client_job_key}" AND
                  worker_nonce="${worker_nonce}"`
    };
    let results:spanner.QueryResult[] = await this.spannerDatabase.run(query);
    if(results.length === 0){
      throw new NoResultsError('getWorkerAnswers: Resulted in empty query response');
    }
    let answerRows = results[0].map(
      row => parseSpannerOutputRow<db_types.AnswerRow>(row));

    return answerRows;
  }

  public async getAllQuestionGroups() {
    const query : spanner.Query = {
      sql: `SELECT question_group_id, COUNT(1) as number_of_questions FROM Questions
            GROUP BY question_group_id`
    };
    let results:spanner.QueryResult[] = await this.spannerDatabase.run(query);
    if(results.length === 0){
      throw new NoResultsError('getAllQuestionGroups: Resulted in empty query response');
    }
    return results[0].map(r => parseSpannerOutputRow<QuestionGroupRow>(r));
  }

  public async getJobQuality(client_job_key:string)
      : Promise<QualitySummary> {
    db_types.assertClientJobKey(client_job_key);
    const query : spanner.Query = {
      sql: `SELECT AVG(answer_score) as mean_score
            FROM Answers as a
                 JOIN Questions as q
                   ON a.question_id = q.question_id
            WHERE a.client_job_key="${client_job_key}" AND
                  q.type != 'training'`
    };
    let results:spanner.QueryResult[] = await this.spannerDatabase.run(query);
    if(results.length === 0 || results[0].length === 0){
      throw new NoResultsError('getWorkerAnswers: Resulted in empty query response');
    }
    if(results[0].length !== 1){
      throw new ResultsError('Strangely resulted in not 1 row', results);
    }
    return parseSpannerOutputRow<QualitySummary>(results[0][0]);
  }

  public async getWorkerQuality(client_job_key:string, worker_nonce:string)
      : Promise<QualitySummary> {
    db_types.assertClientJobKey(client_job_key);
    db_types.assertWorkerNonce(worker_nonce);
    const query : spanner.Query = {
      sql: `SELECT AVG(answer_score) as mean_score
            FROM Answers as a
                 JOIN Questions as q
                 ON a.question_id = q.question_id
            WHERE a.client_job_key="${client_job_key}" AND
                  q.type = 'training' AND
                  a.worker_nonce="${worker_nonce}"`
    };
    let results:spanner.QueryResult[] = await this.spannerDatabase.run(query);
    if(results.length === 0 || results[0].length === 0){
      throw new NoResultsError('getWorkerAnswers: Resulted in empty query response');
    }
    if(results[0].length !== 1){
      throw new ResultsError('Strangely resulted in not 1 row', results);
    }
    return parseSpannerOutputRow<QualitySummary>(results[0][0]);
  }

  public async getQuestionAnswers(client_job_key:string, question_id:string)
      : Promise<db_types.AnswerRow[]> {
    db_types.assertClientJobKey(client_job_key);
    // Note: This should never happen if DB is well formed. But put here defensively
    // in case of manual DB hackery, which we don't want to do wrong.
    db_types.assertQuestionId(question_id);
    const query : spanner.Query = {
      sql: `SELECT answer_id, timestamp, worker_nonce, answer FROM Answers
            WHERE client_job_key="${client_job_key}" AND
                  question_id="${question_id}"`
    };
    let results:spanner.QueryResult[] = await this.spannerDatabase.run(query);
    if(results.length === 0){
      throw new NoResultsError('getWorkerAnswers: Resulted in empty query response');
    }
    let answerRows = results[0].map(
      row => parseSpannerOutputRow<db_types.AnswerRow>(row));
    return answerRows;
  }

  public async getJobAnswers(client_job_key:string)
      : Promise<db_types.AnswerRow[]> {
    let clientJob = await this.getClientJob(client_job_key);
    // Note: This should never happen if DB is well formed. But put here defensively
    // in case of manual DB hackery, which we don't want to do wrong.
    db_types.assertClientJobKey(client_job_key);
    db_types.assertQuestionGroupId(clientJob.question_group_id);
    const query : spanner.Query = {
      sql: `SELECT question_id, answer_id, timestamp, worker_nonce, answer FROM Answers
            WHERE client_job_key="${client_job_key}" AND
                  question_group_id="${clientJob.question_group_id}"`
    };
    let results:spanner.QueryResult[] = await this.spannerDatabase.run(query);
    if(results.length === 0){
      throw new NoResultsError('getWorkerAnswers: Resulted in empty query response');
    }
    let answerRows = results[0].map(
      row => parseSpannerOutputRow<db_types.AnswerRow>(row));
    return answerRows;
  }

  public async updateQuestions(questions:db_types.QuestionRow[])
    : Promise<void> {
      return this.questionTable.update(
        questions.map(q => db_types.prepareQuestionSpannerInputRow(q)));
  };

  // public async setQuestionAnswers(question_group_id:string, question_id:string,
  //     question_type:string, accepted_answer:string)
  //     : Promise<void> {

  //   db_types.assertQuestionType(question_type);
  //   db_types.assertQuestionId(question_id);
  //   db_types.assertQuestionGroupId(question_group_id);

  //   return this.questionTable.update([
  //         { question_group_id: question_group_id,
  //           question_id: question_id,
  //           type: question_type,
  //           accepted_answer: accepted_answer }])
  //       .then(() => {
  //         console.log('Updated data.');
  //       });
  // }
}