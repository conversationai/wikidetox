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
  question: db_types.Question;
  question_id: string;
}

export interface AnswerToQuestion {
  answer_id: string | null; // /^\w+$/
  answer: questionaire.Answer; // JSON
  client_job_key: string; // /^\w+$/
  question_id: string; // /^\w+$/
  worker_nonce: string;
}

export interface QualitySummary {
  mean_score : number;
  answer_count : number;
}

export interface ScoredAnswer {
  // Primary index:
  answer_id : string;
  worker_nonce : string;
  question_group_id : string;
  question_id : string;
  client_job_key : string;
  // correct answer
  accepted_answers : questionaire.QuestionScores;
  // actual answer
  answer : questionaire.Answer; // JSON;
  // score for the answer
  answer_score : number;
}

export interface QuestionGroupRow {
  question_group_id : string;
  question_count : number;
}

export interface TestAnswerRow {
  question_group_id : string;
  question_id : string;
  answer_id : string;
  worker_nonce : string;
  answer_score : string;
}

export class NoResultsError extends Error {}

export class InValidAnswerError extends Error {}

export class ResultsError<T> extends Error {
  constructor(message:string, public results: T[][]) {
    super(message);
  }
}

// TODO(ldixon): when/if sessions expire, we need to reconnet.
// See: https://cloud.google.com/spanner/docs/sessions#keep_an_idle_session_alive
// (Yes, we do try to keep it alive, but we should still fail and recover
// gracefully if connections drop).

// CrowdsourceDB takes responsibility for checking parameters won't
// result in SQL injection or other bad things.
export class CrowdsourceDB {
  // TODO(ldixon): consider a typed table wrapper that does the natural
  // and sensible JSON interpretatin for insert, update, and list-returning
  // queries, and single-element queries.
  public answerTable: spanner.Table; // <AnswerRow>;
  public questionTable: spanner.Table; // <QuestionRow>;
  public clientJobTable: spanner.Table; // <ClientJobRow>;

  constructor(public spannerDatabase : spanner.Database) {
    // Instantiate Spanner table objects
    this.answerTable = this.spannerDatabase.table('Answers');
    this.questionTable = this.spannerDatabase.table('Questions');
    this.clientJobTable = this.spannerDatabase.table('ClientJobs');
  }

  public close() : Promise<void> {
    return new Promise((resolve, _reject) => this.spannerDatabase.close(resolve));
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
    return db_types.parseOutputRow<db_types.ClientJobRow>(results[0][0]);
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
    let clientJobRows = results[0].map(row => db_types.parseOutputRow<db_types.ClientJobRow>(row));
    return clientJobRows;
  }

  // Get all the answers to questions.
  public async getScoredAnswers(client_job_key?:string) : Promise<ScoredAnswer[]> {
    let jobKeyRestriction = '';
    if (client_job_key) {
      db_types.assertClientJobKey(client_job_key);
      jobKeyRestriction = `AND a.client_job_key = '${client_job_key}'`;
    }
    const query : spanner.Query = {
      sql: `SELECT q.question_group_id, q.question_id, a.client_job_key, a.answer_id, a.worker_nonce,
                   q.accepted_answers, a.answer, a.answer_score
            FROM Answers as a
              JOIN Questions as q
              ON a.question_id = q.question_id
            WHERE (q.accepted_answers IS NOT NULL AND CHAR_LENGTH(q.accepted_answers) > 0)
                  ${jobKeyRestriction}`
    };
    let results:spanner.QueryResult[] = await this.spannerDatabase.run(query);
    if(results.length === 0){
      throw new NoResultsError('Resulted in empty query response');
    }
    let scoredAnswerRows = results[0].map(
      row => db_types.parseOutputRow<ScoredAnswer>(row));
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
      row => db_types.parseOutputRow<QuestionToAnswer>(row));
    return questionRows;
  }

  public async getQuestionToAnswer(client_job_key:string, question_id:string) : Promise<db_types.QuestionRow> {
    db_types.assertQuestionId(question_id);
    db_types.assertClientJobKey(client_job_key);
    const query : spanner.Query = {
      sql: `SELECT q.question_id, q.question, c.answers_per_question,
              COUNT(a.question_id) as answer_count
            FROM ClientJobs as c
              JOIN Questions as q
                ON c.question_group_id = q.question_group_id
              LEFT JOIN Answers as a
                ON a.question_id = q.question_id
            WHERE c.client_job_key = "${client_job_key}"
              AND q.question_id = "${question_id}"
            GROUP BY q.question_id, q.question, c.answers_per_question
            `
    };
    let results:spanner.QueryResult[] = await this.spannerDatabase.run(query);
    if(results.length === 0 || results[0].length === 0){
      throw new NoResultsError('getQuestionToAnswer: Resulted in empty query response');
    }
    if(results[0].length !== 1){
      throw new ResultsError('Strangely resulted in not 1 row', results);
    }
    return db_types.parseOutputRow<db_types.QuestionRow>(results[0][0]);
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
      row => db_types.parseOutputRow<QuestionToAnswer>(row));
    return questionRows;
  }


  public async getClientJobQuestions(
      client_job_key:string,
      training: boolean) : Promise<QuestionToAnswer[]> {
    db_types.assertClientJobKey(client_job_key)

    // TODO(ldixon) make this part of a transaction: this is
    // mostly used to make sure the job actually exists. It
    // will also allow us to not use the join below, for whatever
    // that's worth.
    this.getClientJob(client_job_key);
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
      row => db_types.parseOutputRow<QuestionToAnswer>(row));
    return questionRows;
  }

  public async getQuestion(question_group_id:string, question_id:string) : Promise<db_types.QuestionRow> {
    db_types.assertQuestionId(question_id)
    db_types.assertQuestionGroupId(question_group_id)
    const query : spanner.Query = {
      sql: `SELECT * FROM Questions
            WHERE question_group_id="${question_group_id}" AND question_id="${question_id}"`
    };
    let results:spanner.QueryResult[] = await this.spannerDatabase.run(query);
    if(results.length === 0 || results[0].length === 0){
      throw new NoResultsError('getQuestion: Resulted in empty query response');
    }
    if(results[0].length !== 1){
      throw new ResultsError('Strangely resulted in not 1 row', results);
    }
    return db_types.parseOutputRow<db_types.QuestionRow>(results[0][0]);
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
    return results[0].map(r => db_types.parseOutputRow<db_types.QuestionRow>(r));
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
    db_types.assertClientJobKey(answer.client_job_key);
    let clientJob : db_types.ClientJobRow = await this.getClientJob(answer.client_job_key);
    db_types.assertQuestionId(answer.question_id);
    let question : db_types.QuestionRow = await this.getQuestion(
        clientJob.question_group_id, answer.question_id);
    let answerObj : {};
    if (typeof(answer.answer) === "string") {
      answerObj = JSON.parse(answer.answer);
    } else {
      answerObj = answer.answer;
    }
    if(!questionaire.answerMatchesSchema(clientJob.answer_schema, answerObj)) {
      throw new InValidAnswerError('answer does not match schema: ' +
          JSON.stringify(clientJob.answer_schema, null, 2) + '\n '+
          JSON.stringify(answerObj, null, 2));
    }
    let answer_score :number | null = null;
    if (question.accepted_answers) {
      console.log(answerObj);
      answer_score = questionaire.answerScore(question.accepted_answers, answerObj);
    }

    // TODO(ldixon): don't allow multiple submission per user?
    let answerRow : db_types.AnswerRow = {
      answer: answerObj,
      answer_id: answer.answer_id,
      client_job_key: answer.client_job_key,
      question_id: answer.question_id,
      question_group_id: question.question_group_id,
      answer_score: answer_score,
      worker_nonce: answer.worker_nonce,
      timestamp: new Date()
    };
    return this.answerTable.insert([db_types.prepareInputRow(answerRow)]);
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
    return this.clientJobTable.insert([db_types.prepareInputRow(clientJob)]);
  }

  public async updateClientJob(clientJob:db_types.ClientJobRow) {
    db_types.assertClientJobKey(clientJob.client_job_key);
    db_types.assertQuestionGroupId(clientJob.question_group_id);
    // TODO(ldixon): check answers_per_question & give nice error.
    // if(!regexp_strict_positive_number.test(client_job_row.answers_per_question)) {
    //   res.status(400).send('bad param: answers_per_question: ' +
    //       JSON.stringify(client_job_row.answers_per_question));
    //   return;
    // }
    return this.clientJobTable.update([db_types.prepareInputRow(clientJob)]);
  }

  public async addQuestions(questions:db_types.QuestionRow[]) {
    // TODO: validate questions have valid ids.
    let spannerInputRows : spanner.InputRow[] =
      questions.map(q => {
        db_types.assertQuestionId(q.question_id);
        db_types.assertQuestionGroupId(q.question_group_id);
        return db_types.prepareInputRow(q);
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
      row => db_types.parseOutputRow<db_types.AnswerRow>(row));

    return answerRows;
  }

  public async getAllQuestionGroups() {
    const query : spanner.Query = {
      sql: `SELECT question_group_id, COUNT(1) as question_count FROM Questions
            GROUP BY question_group_id`
    };
    let results:spanner.QueryResult[] = await this.spannerDatabase.run(query);
    if(results.length === 0){
      throw new NoResultsError('getAllQuestionGroups: Resulted in empty query response');
    }
    return results[0].map(r => db_types.parseOutputRow<QuestionGroupRow>(r));
  }

  public async getJobQuality(client_job_key:string)
      : Promise<QualitySummary> {
    db_types.assertClientJobKey(client_job_key);
    const query : spanner.Query = {
      sql: `SELECT * FROM
              (SELECT COUNT(*) as toanswer_count
                FROM Answers as a
                    JOIN Questions as q
                      ON a.question_id = q.question_id
                WHERE a.client_job_key="${client_job_key}")
              CROSS JOIN
              (SELECT AVG(a.answer_score) as toanswer_mean_score
                FROM Answers as a
                    JOIN Questions as q
                      ON a.question_id = q.question_id
                WHERE a.client_job_key="${client_job_key}" AND
                      q.type != 'toanswer')`
    };
    let results:spanner.QueryResult[] = await this.spannerDatabase.run(query);
    if(results.length === 0 || results[0].length === 0){
      throw new NoResultsError('getWorkerAnswers: Resulted in empty query response');
    }
    if(results[0].length !== 1){
      throw new ResultsError('Strangely resulted in not 1 row', results);
    }
    return db_types.parseOutputRow<QualitySummary>(results[0][0]);
  }

  public async getJobTestAnswers(client_job_key:string)
      : Promise<TestAnswerRow[]> {
    db_types.assertClientJobKey(client_job_key);
    const query : spanner.Query = {
      sql: `SELECT
              q.question_group_id, q.question_id,
              a.answer_id, a.worker_nonce,
              a.answer_score
            FROM Answers as a
                 JOIN Questions as q
                   ON a.question_id = q.question_id
            WHERE a.client_job_key="${client_job_key}" AND
                  q.type != 'toanswer'`
    };
    let results:spanner.QueryResult[] = await this.spannerDatabase.run(query);
    if(results.length === 0){
      throw new NoResultsError('getJobTestAnswers: Resulted in empty query response');
    }
    return results[0].map(r => db_types.parseOutputRow<TestAnswerRow>(r));
  }

  public async getWorkerQuality(client_job_key:string, worker_nonce:string)
      : Promise<QualitySummary> {
    db_types.assertClientJobKey(client_job_key);
    db_types.assertWorkerNonce(worker_nonce);
    const query : spanner.Query = {
      sql: `
      SELECT * FROM
        (SELECT COUNT(*) as answer_count
          FROM Answers as a
              JOIN Questions as q
                ON a.question_id = q.question_id
          WHERE a.client_job_key="${client_job_key}" AND
                a.worker_nonce="${worker_nonce}")
        CROSS JOIN
        (SELECT AVG(a.answer_score) as mean_score
          FROM Answers as a
              JOIN Questions as q
                ON a.question_id = q.question_id
          WHERE a.client_job_key="${client_job_key}" AND
                q.type != 'toanswer' AND
                a.worker_nonce="${worker_nonce}")
        `
    };
    let results:spanner.QueryResult[] = await this.spannerDatabase.run(query);
    if(results.length === 0 || results[0].length === 0){
      throw new NoResultsError('getWorkerAnswers: Resulted in empty query response');
    }
    if(results[0].length !== 1){
      throw new ResultsError('Strangely resulted in not 1 row', results);
    }
    return db_types.parseOutputRow<QualitySummary>(results[0][0]);
  }

  public async getWorkerScoredAnswers(client_job_key:string, worker_nonce:string)
      : Promise<ScoredAnswer[]> {
    db_types.assertClientJobKey(client_job_key);
    db_types.assertWorkerNonce(worker_nonce);
    const query : spanner.Query = {
      sql: `SELECT *
          FROM Answers as a
              JOIN Questions as q
                ON a.question_id = q.question_id
          WHERE a.client_job_key="${client_job_key}" AND
                q.type = 'training' AND
                a.worker_nonce="${worker_nonce}"
        `
    };
    let results:spanner.QueryResult[] = await this.spannerDatabase.run(query);
    if(results.length === 0 || results[0].length === 0){
      throw new NoResultsError('getWorkerAnswers: Resulted in empty query response');
    }
    return results[0].map((row) => db_types.parseOutputRow<ScoredAnswer>(row));
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
      row => db_types.parseOutputRow<db_types.AnswerRow>(row));
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
      row => db_types.parseOutputRow<db_types.AnswerRow>(row));
    return answerRows;
  }

  public async updateAnswers(answers:db_types.AnswerRow[])
    : Promise<void> {
      return this.answerTable.update(
        answers.map(a => db_types.prepareInputRow(a)));
  };

  public async updateQuestions(questions:db_types.QuestionRow[])
    : Promise<void> {
      return this.questionTable.update(
        questions.map(q => db_types.prepareInputRow(q)));
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