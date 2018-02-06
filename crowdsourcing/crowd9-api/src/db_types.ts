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
import * as questionaire from './questionaire';

export interface Question {
  // A fake field to make this type unique: fake nominal typing using npm namespace.
  __type__: '@conversationai/wikidetox:db_types.Question';
}

// Spanner Row Representations in JS.
//
// Note: Cloud Spanner interprets Node.js numbers as FLOAT64s, so
// in the row format, they are treated as strings (spanner does
// the conversion to INT64s when appropriate)
export interface AnswerRow {
  // Optional client specified answer id.
  answer_id: string | null; // /^\w+$/
  // Details of what this is an answer for: the primary index.
  client_job_key: string; // /^\w+$/
  question_group_id: string; // /^\w+$/
  question_id: string; // /^\w+$/
  worker_nonce: string;
  // The answer
  answer: questionaire.Answer; // JSON
  // Computed score for the answer.
  answer_score: number | null;  // if null, then question.type == 'toanswer'
  // TODO(ldixon): consider moving to using javascript Date here.
  timestamp: Date;  // Set by server, not by spanner and not by client. String representation of date.
}
export interface QuestionRow {
  question: Question; // JSON
  question_group_id: string; // /^\w+$/
  question_id: string; // /^\w+$/
  // 'training' is for questions where the answer is shown to the
  // client. 'test' are hidden from the client and used to measure
  // quality over time. 'toanswer' are for the client to provide answers to.
  // The client must be unable to distingish 'test' from 'toanswer' questions.
  type: 'training' | 'test' | 'toanswer';
  // (accepted_answers == null) iff ('type' == 'toanswer')
  // TODO(ldixon): refactor.
  accepted_answers: questionaire.QuestionScores | null; // JSON
}
export interface ClientJobRow {
  answers_per_question: number;  // /^[1-9]\d*$/
  client_job_key: string; // /^\w+$/
  description: string;
  title: string;
  answer_schema : questionaire.QuestionSchema;  // JSON schema for kinds of acceptable answers.
  question_group_id: string; // /^\w+$/
  // Status is not really used right now; currently everything is expected to
  // be 'setup'
  status: 'setup' | 'inprogress' | 'paused' | 'completed';
}

// Helper function to allow "field: undefined" to be treated appropriately (for queries that
// are patches to update fields).
export function deleteUndefindValueKeys(row : spanner.InputRow) : spanner.InputRow {
  for (let k in row) {
    if (row[k] === undefined) {
      delete row[k];
    }
  }
  return row;
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
export const valid_id_regexp = new RegExp(/^(\w|\.|\-|\:|\#)+$/);
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


interface SpannerFieldHandler<T> {
  field_name : string;
  toSpannerInputField(x:T) : spanner.InputField;
  fromSpannerResultField(row:spanner.ResultField) : T | null;
}

// TODO(ldixon): add fancier validation, more subtypes, e.g. for checking fields match specific T.
class JsonFieldHandler<T> implements SpannerFieldHandler<T> {
  constructor(public field_name: string) {
    this.field_name = field_name;
  }
  public toSpannerInputField(x:T) : spanner.InputField {
    return JSON.stringify(x);
  }
  public fromSpannerResultField(field:spanner.ResultField) : T | null {
    if(field === null) {
      return null;
    }
    if(typeof(field) !== 'string') {
      console.log('Error: field:');
      console.dir(field);
      throw Error(`For ${this.field_name}: expected json field:string, not: ${typeof(field)}`);
    }
    return JSON.parse(field);
  }
}

// TODO(ldixon): add additional constraints, e.g. regexp matching.
class StringFieldHandler implements SpannerFieldHandler<string> {
  constructor(public field_name: string) {
    this.field_name = field_name;
  }
  public toSpannerInputField(input:string) : spanner.InputField { return input; }
  public fromSpannerResultField(field:spanner.ResultField) : string | null {
    if(!(field === null || typeof(field) === 'string')) {
      console.log('Error: field:');
      console.dir(field);
      throw Error(`For ${this.field_name}: expected field:string, not: ${typeof(field)}`);
    }
    return field;
  }
}

// TODO(ldixon): add option for can be null or not.
class IntFieldHandler implements SpannerFieldHandler<number> {
  constructor(public field_name: string) {
    this.field_name = field_name;
  }
  public toSpannerInputField(input:number) : spanner.InputField {
    return spanner.int(input);
  }
  public fromSpannerResultField(field:spanner.ResultField) : number | null {
    if(typeof(field) === 'string') {
      throw Error(`For ${this.field_name}: expected field.value:string, but field:string`);
    } else if (field instanceof Date) {
      throw Error(`For ${this.field_name}: expected field.value:string, but field:Date`);
    } else if (field === null) {
      return null;
    }
    //  else if (x.value === null) {
    //   throw Error('Expected field.value to not be null')
    // }
    return parseInt(field.value);
  }
}

class FloatFieldHandler implements SpannerFieldHandler<number> {
  constructor(public field_name: string) {
    this.field_name = field_name;
  }
  public toSpannerInputField(input:number) : spanner.InputField {
    return spanner.float(input);
  }
  public fromSpannerResultField(field:spanner.ResultField) : number | null {
    if(typeof(field) === 'string') {
      throw Error(`For ${this.field_name}: expected field.value:string, but field:string`);
    } else if (field instanceof Date) {
      throw Error(`For ${this.field_name}: expected field.value:string, but field:Date`);
    } else if (field === null) {
      return null;
    }
    return parseFloat(field.value);
  }
}

// class dateFieldHandler implements SpannerFieldHandler<Date> {
//   constructor(public field_name: string) {
//     this.field_name = field_name;
//   }
//   public toSpannerInputField(x:Date) : spanner.InputField {
//     return x.toJSON();
//   }
//   public fromSpannerResultField(x:spanner.ResultField) : Date {
//     if (!(x instanceof Date)) {
//       throw Error('dateFieldHandler expected field : Date')
//     }
//     return x;
//   }
// }

class TimestampFieldHandler implements SpannerFieldHandler<Date> {
  constructor(public field_name: string) {
    this.field_name = field_name;
  }
  public toSpannerInputField(field:Date) : spanner.InputField {
    return field.toJSON();
  }
  public fromSpannerResultField(field:spanner.ResultField) : Date | null {
    if (!(field === null || field instanceof Date)) {
      throw Error(`For ${this.field_name}: expected field:Date, but field:${typeof(field)}`);
    }
    return field;
  }
}

interface HandlerSet { [field_name:string] : SpannerFieldHandler<any>; };

let handlers : SpannerFieldHandler<{}>[] = [
  // Answer
  new StringFieldHandler('answer_id'),
  new StringFieldHandler('client_job_key'),
  new StringFieldHandler('question_group_id'),
  new StringFieldHandler('question_id'),
  new StringFieldHandler('worker_nonce'),
  new JsonFieldHandler<questionaire.Answer>('answer'),
  new FloatFieldHandler('answer_score'),
  new TimestampFieldHandler('timestamp'),
  // Question
  new JsonFieldHandler<Question>('question'),
  new StringFieldHandler('worker_nonce'),
  new StringFieldHandler('question_id'),
  new StringFieldHandler('type'),
  new JsonFieldHandler<questionaire.QuestionScores>('accepted_answers'),
  // ClientJobRow
  new IntFieldHandler('answers_per_question'),
  new StringFieldHandler('client_job_key'),
  new StringFieldHandler('description'),
  new StringFieldHandler('title'),
  new JsonFieldHandler<questionaire.QuestionSchema>('answer_schema'),
  // question_group_id is already defined above.
  new StringFieldHandler('status'),
  // Other fields
  new IntFieldHandler('question_count'),
  // Job Quality summary
  new FloatFieldHandler('toanswer_mean_score'),
  new IntFieldHandler('toanswer_count'),
  // Worker quality summary
  new IntFieldHandler('answer_count'),
  new FloatFieldHandler('mean_score'),
];

function addHandler(handlers : HandlerSet, handler : SpannerFieldHandler<{}>)
    : HandlerSet {
  handlers[handler.field_name] = handler;
  return handlers;
}
const handlerSet = handlers.reduce<HandlerSet>(addHandler, {});


// TODO(ldixon): see if this can be pushed into the spanner client library.
export function prepareInputRow<T>(x:T) : spanner.InputRow {
  let row : spanner.InputRow = {};
  for (let field_name in x) {
    if(!(field_name in handlerSet)) {
      console.error(`Field ${field_name} does not have a handler and so cannot be interpreted.`);
      break;
    }
    row[field_name] = handlerSet[field_name].toSpannerInputField(x[field_name]);
  }
  return row;
}

// TODO(ldixon): see if this can be pushed into the spanner client library.
export function parseOutputRow<T>(row: spanner.ResultRow) : T {
  let output : { [field_name:string] : {} } = {};
  for (let field of row) {
    if(!(field.name in handlerSet)) {
      console.error(`Field ${field.name} does not have a handler and so cannot be interpreted.`);
      break;
    }
    output[field.name] = handlerSet[field.name].fromSpannerResultField(field.value);
  }
  return output as any as T;
}

// export function prepareAnswerSpannerInputRow(answer:AnswerRow) : spanner.InputRow {
//   return deleteUndefindValueKeys({
//     answer: JSON.stringify(answer.answer),
//     answer_id: answer.answer_id,
//     client_job_key: answer.client_job_key,
//     question_id: answer.question_id,
//     question_group_id: answer.question_group_id,
//     answer_score: spanner.float(answer.answer_score),
//     worker_nonce: answer.worker_nonce,
//     timestamp: answer.timestamp
//   });
// }

// export function prepareClientJobSpannerInputRow(clientJob:ClientJobRow) : spanner.InputRow {
//   return deleteUndefindValueKeys({
//     answers_per_question: spanner.int(clientJob.answers_per_question),
//     client_job_key: clientJob.client_job_key,
//     description: clientJob.description,
//     question_group_id: clientJob.question_group_id,
//     answer_schema: JSON.stringify(clientJob.answer_schema),
//     status: clientJob.status,
//     title: clientJob.title,
//   });
// }

// export function prepareQuestionSpannerInputRow(questionRow:QuestionRow) : spanner.InputRow {
//   return deleteUndefindValueKeys({
//     accepted_answers: JSON.stringify(questionRow.accepted_answers),
//     question: JSON.stringify(questionRow.question),
//     question_group_id: questionRow.question_group_id,
//     question_id: questionRow.question_id,
//     type: questionRow.type
//   });
// }

// interface SpannerOutputRow { [key:string] : string | number | null };

// // Convert spanner's output row representation into a more natural JSON
// // representation that we can easily have typescript schema for.
// function parseSpannerOutputRow<T>(row: spanner.ResultRow) : T {
//   let parsedRow : SpannerOutputRow = {};
//   for(let entry of row) {
//     // console.log(row);
//     if(entry.value === null) {
//       parsedRow[entry.name] = null;
//     } else if(typeof(entry.value) === 'string') {
//       parsedRow[entry.name] = entry.value;
//     } else if(entry.value instanceof Date) {
//       parsedRow[entry.name] = entry.value.toJSON();
//     } else if(typeof(entry.value.value) === 'string') {
//       // TODO(this isn't safe for big INTs: probably need to change schema to be INT32?)
//       let parsedInt = parseInt(entry.value.value);
//       if (parsedInt !== null && parsedInt !== undefined) {
//         parsedRow[entry.name] = parsedInt;
//       } else {
//         console.warn('*** entry value type being treated as string: ' + entry.value.value);
//         parsedRow[entry.name] = entry.value.value;
//       }
//     } else {
//       console.error('*** entry value type being treated as int; type: ', typeof(entry.value));
//       console.error('*** entry value type being treated as int; value: ', JSON.stringify(entry.value, null, 2));
//       parsedRow[entry.name] = null;
//     }
//   }
//   return parsedRow as any as T;
// }


