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
import * as spanner from '@google-cloud/spanner';

// Spanner Row Representations in JS.
//
// Note: Cloud Spanner interprets Node.js numbers as FLOAT64s, so
// in the row format, they are treated as strings (spanner does
// the conversion to INT64s when appropriate)
export interface AnswerRow {
  // Optional client specified answer id.
  answer_id: string | null; // /^\w+$/
  // Details of what this is an answer for
  client_job_key: string; // /^\w+$/
  question_group_id: string; // /^\w+$/
  question_id: string; // /^\w+$/
  worker_nonce: string;
  // The answer
  answer: string; // JSON
  // Computed score for the answer.
  answer_score: number | null;  // if null, then question.type == 'toanswer'
  // TODO(ldixon): consider moving to using javascript Date here.
  timestamp: string;  // Set by server, not by spanner and not by client. String representation of date.
}
export interface QuestionRow {
  question: string; // JSON
  question_group_id: string; // /^\w+$/
  question_id: string; // /^\w+$/
  // 'training' is for questions where the answer is shown to the
  // client. 'test' are hidden from the client and used to measure
  // quality over time. 'toanswer' are for the client to provide answers to.
  // The client must be unable to distingish 'test' from 'toanswer' questions.
  type: 'training' | 'test' | 'toanswer';
  // (accepted_answers == null) iff ('type' == 'toanswer')
  accepted_answers: string | null; // JSON
}
export interface ClientJobRow {
  answers_per_question: number;  // /^[1-9]\d*$/
  client_job_key: string; // /^\w+$/
  description: string;
  title: string;
  question_group_id: string; // /^\w+$/
  status: 'setup' | 'inprogress' | 'paused' | 'completed';
}


// Converstion from the output format of spanner queries back into the
// format that can be inserted into spanner.
// TODO(ldixon): see if this can be pushed into the spanner client library.
export function prepareAnswerSpannerInputRow(answer:AnswerRow) : spanner.InputRow {
  return {
    answer: answer.answer,
    answer_id: answer.answer_id,
    client_job_key: answer.client_job_key,
    question_id: answer.question_id,
    question_group_id: answer.question_group_id,
    answer_score: spanner.float(answer.answer_score),
    worker_nonce: answer.worker_nonce,
    timestamp: answer.timestamp
  };
}

export function prepareClientJobSpannerInputRow(clientJob:ClientJobRow) : spanner.InputRow {
  return {
    answers_per_question: spanner.int(clientJob.answers_per_question),
    client_job_key: clientJob.client_job_key,
    description: clientJob.description,
    question_group_id: clientJob.question_group_id,
    status: clientJob.status,
    title: clientJob.title,
  };
}

export function prepareQuestionSpannerInputRow(questionRow:QuestionRow) : spanner.InputRow {
  return {
    accepted_answers: questionRow.accepted_answers,
    question: questionRow.question,
    question_group_id: questionRow.question_group_id,
    question_id: questionRow.question_id,
    type: questionRow.type
  };
}


// Parameters can only contain alphanumeric, underscores, ., -, :, or #.
export class BadQuestionTypeError extends Error {}
export const valid_question_type_regexp = new RegExp(/^(training|test|toanswer)$/);
export function assertQuestionType(type: string) {
  if(!valid_question_type_regexp.test(type)) {
    throw new BadQuestionTypeError(
      `Question type must be 'training' | 'test' | 'toanswer', not: ${type}`);
  }
}


// Parameters can only contain alphanumeric, underscores, ., -, :, or #.
export const valid_id_regexp = new RegExp(/^(\w|\.\-\:\#)+$/);
// const regexp_strict_positive_number = new RegExp(/^[1-9]\d*$/);

export class BadIdNameError extends Error {}

export function assertRexExpId(id_kind:string, id: string) {
  if(!valid_id_regexp.test(id)) {
    throw new BadIdNameError(
      `${id_kind} must be an alpha-numeric or underscore string, not: ${id}`);
  }
}

export let assertClientJobKey = assertRexExpId.bind(null, 'client_job_key');
export let assertQuestionId = assertRexExpId.bind(null, 'question_id');
export let assertQuestionGroupId = assertRexExpId.bind(null, 'question_group_id');
export let assertAnswerId = assertRexExpId.bind(null, 'question_group_id');
export let assertWorkerNonce = assertRexExpId.bind(null, 'worker_nonce');