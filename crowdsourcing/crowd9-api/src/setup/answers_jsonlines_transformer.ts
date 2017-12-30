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

  node build/server/setup/answers_jsonlines_transformer.js \
    --infile="./tmp/Answers.json" \
    --infile="./tmp/Answers2.json"
*/

import * as yargs from 'yargs';
import * as db_types from '../db_types';
import * as fs from 'fs';
import * as readline from 'readline';
import * as stream from 'stream';

// Command line arguments.
interface Params {
  infile:string,
  outfile:string,
};

// "{\"identityHate\":\"NotAtAll\",\"threat\":\"NotAtAll\",\"readableAndInEnglish\":\"Yes\",\"toxic\":\"Somewhat\"}"

interface AnswerT1 {
  answer : string,
  answer_id ?: string,
  client_job_key: string,
  question_group_id: string,
  question_id: string,
  timestamp: string,
  answer_score ?: string,
  worker_nonce: string
}

type AnswerPartType = 'insult' | 'obscene' | 'comments' | 'identityHate' | 'threat'
| 'readableAndInEnglish' | 'toxic';

const ANSWER_PART_TYPES : AnswerPartType[] = ['insult', 'obscene', 'comments', 'identityHate', 'threat',
                           'readableAndInEnglish', 'toxic'];

interface AnswerT2 {
  answer : string,
  answer_part_id : AnswerPartType,
  answer_id ?: string,
  client_job_key: string,
  question_group_id: string,
  question_id: string,
  timestamp: string,
  answer_score ?: string,
  worker_nonce: string
}

async function main(args : Params) {
    let instream = fs.createReadStream(args.infile);
    let outstream = fs.createWriteStream(args.outfile, {flags: 'w', defaultEncoding: 'utf-8'});
    let rl = readline.createInterface(instream, outstream);

    let lineCount = 0;
    let answerPartCounts : { [key:string]: number } = {};
    let answerPartCount = 0;
    let missingAnswerCount = 0;
    let strangeAnswerCount = 0;

    rl.on('line', async function(line) {
      let obj : AnswerT1 = JSON.parse(line);
      let answerObj = JSON.parse(obj.answer);

      let containSomeAnswer = false;
      for (let answer_part of ANSWER_PART_TYPES) {
        if (answer_part in answerObj) {
          containSomeAnswer = true;
          let obj2 : AnswerT2 = {} as any;
          Object.assign(obj2, obj);
          obj2.answer = answerObj[answer_part];
          if(answer_part !== 'comments' && obj2.answer !== null) {
            if (obj2.answer.toLowerCase) { obj2.answer = obj2.answer.toLowerCase(); }
            else {
              console.warn(`Answer is strange for: ${line}`);
              strangeAnswerCount += 1;
              continue;
            }
          }
          obj2.answer_part_id = answer_part;
          if (!(answer_part in answerPartCounts)) {
            answerPartCounts[answer_part] = 0;
          }
          answerPartCounts[answer_part] += 1;
          answerPartCount +=1;
          outstream.write(`${JSON.stringify(obj2)}\n`);
        }
      }
      if (!containSomeAnswer) {
        missingAnswerCount += 1;
        console.error(`Missing valid answer type for: ${line}`);
      }
    });

    rl.on('close', function() {
      outstream.end();
      console.log(`lineCount: ${lineCount}; answerPartCount: ${answerPartCount}`);
      console.log(`missingAnswerCount: ${missingAnswerCount}; strangeAnswerCount: ${strangeAnswerCount}`);
      console.log(`answerPartCounts: ${JSON.stringify(answerPartCounts, null, 2)}`);
    });
}

let args = yargs
    .option('infile', {
        describe: 'Input path to JSON-lines file of answers with questions'
    })
    .option('outfile', {
      describe: 'Creted path to JSON-lines file with separate answer_parts'
    })
    .demandOption(['infile', 'outfile'],
        'Please provide at least --infile and --outfile.')
    .help()
    .argv;

main(args as any as Params)
  .then(() => {
    console.log('Success!');
  }).catch(e => {
    console.error('Failed: ', e);
    process.exit(1);
  });