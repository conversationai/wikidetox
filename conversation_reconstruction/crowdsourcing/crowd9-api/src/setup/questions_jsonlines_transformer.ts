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
Usage: Convert answers with multiple parts into separate rows.

  node build/server/setup/questions_jsonlines_transformer.js \
    --infile="./tmp/Question.json" \
    --out_scorings_file="./tmp/Scorings.json" \
    --out_questions_file="./tmp/Questions2.json"
*/

import * as yargs from 'yargs';
import * as db_types from '../db_types';
import * as questionaire from '../questionaire';
import * as fs from 'fs';
import * as byline from 'byline';
import * as stream from 'stream';
import { Transform, Writable } from 'stream';
import { WriteStream, write } from 'fs-extra';
import { INSPECT_MAX_BYTES } from 'buffer';
import * as multiplex_transform from './multiplex_transform';
import { once } from 'cluster';

// Command line arguments.
interface Params {
  infile:string,
  out_questions_file:string,
  out_scorings_file:string,
};

// "{\"identityHate\":\"NotAtAll\",\"threat\":\"NotAtAll\",\"readableAndInEnglish\":\"Yes\",\"toxic\":\"Somewhat\"}"

interface QuestionT1 {
    accepted_answers : string;
    question : string;
    question_group_id : string;
    question_id : string;
    type : string;
}

type AnswerPartType = 'insult' | 'obscene' | 'comments' | 'identityHate' | 'threat'
| 'readableAndInEnglish' | 'toxic';

const ANSWER_PART_TYPES : AnswerPartType[] = ['insult', 'obscene', 'comments', 'identityHate', 'threat',
                           'readableAndInEnglish', 'toxic'];

// "accepted_answers": "{
//   \"readableAndInEnglish\": {\"optional\":true,\"enum\":{\"yes\":1,\"no\":-1}},
//   \"toxicity\":{\"enum\":{\"ok\":-1,\"somewhat\":1,\"very\":0}},
//   \"obscene\":{\"optional\":true,\"enum\":{\"ok\":-1,\"somewhat\":1,\"very\":1}},
//   \"identityHate\":{\"optional\":true,\"enum\":{\"ok\":-1,\"somewhat\":1,\"very\":1}},
//   \"threat\":{\"optional\":true,\"enum\":{\"ok\":-1,\"somewhat\":1,\"very\":1}},
//   \"insult\":{\"optional\":true,\"enum\":{\"ok\":-1,\"somewhat\":1,\"very\":1}}}"

interface QuestionScoring {
  question_group_id : string;
  question_id : string;
  answer_part_id : string;
  answer : string;
  answer_score : number;  // float 64
}

const SCORING_STREAM_NAME = 'scoring';
const QUESTION_STREAM_NAME = 'question';

async function main(args : Params) {
  let lineCount = 0;
  let answerPartCounts : { [key:string]: number } = {};
  let answerPartCount = 0;

  let interpretStream = new multiplex_transform.Multiplex();
  interpretStream.setEncoding('utf-8');
  interpretStream.setInputProcessor((chunk, encoding, pushFn) => {
    let questionObj : QuestionT1 = JSON.parse(chunk);
    lineCount += 1;
    let answersObj : questionaire.QuestionScores = JSON.parse(questionObj.accepted_answers);

    let containSomeAnswer = false;
    let outScoringsStreamPause = false;
    let outQuestionsStreamPause = false;

    for (let answer_part of ANSWER_PART_TYPES) {
      if (answersObj !== null && answer_part in answersObj) {
        containSomeAnswer = true;
        // console.log(answersObj);
        let questionScoring : QuestionScoring = {} as any;
        questionScoring.question_group_id = questionObj.question_group_id;
        questionScoring.question_id = questionObj.question_id
        questionScoring.answer_part_id = answer_part;
        let enumMap = answersObj[answer_part].enum;
        if (enumMap) {
          for (let enumKey in enumMap) {
            questionScoring.answer = enumKey;
            questionScoring.answer_score = enumMap[enumKey];
            pushFn(SCORING_STREAM_NAME, JSON.stringify(questionScoring));
          }
        }

        if (answerPartCount % 100 === 0) {
          console.log(`Next 100. (answerPartCount: ${answerPartCount}; lineCount: ${lineCount})`);
        }

        if (!(answer_part in answerPartCounts)) {
          answerPartCounts[answer_part] = 0;
        }
        answerPartCounts[answer_part] += 1;
        answerPartCount +=1;
      }
    }
  });

  // let outQuestionsStream = fs.createWriteStream(args.out_questions_file,
  //   {flags: 'w', defaultEncoding: 'utf-8'});
  let outScoringsStream = fs.createWriteStream(args.out_scorings_file,
    {flags: 'w', defaultEncoding: 'utf-8'});
  let lineStream = byline.createStream();
  // interpretStream.addOutputStream(QUESTION_STREAM_NAME, outQuestionsStream);
  interpretStream.addOutputStream(SCORING_STREAM_NAME, outScoringsStream);

  let instream = fs.createReadStream(args.infile);
  instream.pause();
  let completedStream = instream.pipe(lineStream).pipe(interpretStream);
  let onceCompleted = new Promise((resolve, reject) => {
    completedStream.on('final', () => {
      console.log(`lineCount: ${lineCount}; answerPartCount: ${answerPartCount}`);
      console.log(`answerPartCounts: ${JSON.stringify(answerPartCounts, null, 2)}`);
      resolve();
    });
    instream.on('error', (e) => { reject(e); });
    instream.resume();
  });

  console.log('waiting to complete');
  await onceCompleted;
  console.log('completed');
  return;
}

let args = yargs
    .option('infile', {
        describe: 'Input path to a JSON-lines Questions'
    })
    .option('out_questions_file', {
      describe: 'Output path for JSON-lines Questions file'
    })
    .option('out_scorings_file', {
      describe: 'Output path for JSON-lines QuestionScorings file'
    })
    .demandOption(['infile', 'out_scorings_file', 'out_questions_file'],
        'Please provide at least --infile, --out_questions_file, --out_scorings_file.')
    .help()
    .argv;

let done = false;
function waiter() {
  setTimeout(() => { if (!done) { waiter(); } }, 200);
}
waiter();

main(args as any as Params)
  .then(() => {
    console.log('Success!');
    done = true;
  })
  .catch(e => {
    console.error('Failed: ', e);
    process.exit(1);
  });