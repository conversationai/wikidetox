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
Usage:

node build/server/setup/upload_with_answers.js \
  --file="./tmp/real_job/with_answers_mini_10x.json" \
  --question_group="wp_x10k_test" \
  --training_fraction=0.2 \
  --action=print

node build/server/setup/upload_with_answers.js \
  --file="./tmp/real_job/with_answers.json" \
  --question_group="wp_x10k_test" \
  --training_fraction=0.2 \
  --action=insert


node build/server/setup/upload_with_answers.js \
  --file="./tmp/real_job/with_answers.json" \
  --question_group="wp_x10k_test" \
  --training_fraction=0.2 \
  --action=print \
  --from_line 2
*/

import * as yargs from 'yargs';
import * as fs from 'fs';
import * as spanner from '@google-cloud/spanner';
import * as readline from 'readline';
import * as db_types from '../db_types';
import * as crowdsourcedb from '../cs_db';
import * as util from './util';
import * as seedrandom from 'seedrandom';

// TODO(ldixon): fix import of this.
const hashjs = require('hash.js');

// Command line arguments.
interface Params {
  file:string,
  question_group:string,
  gcloud_project_id:string,
  spanner_instance:string,
  spanner_db:string,
  action: 'print' | 'update' | 'insert' | 'count',
  random_seed: string;
  training_fraction: number;  // float.
  from_line: number | null;
  to_line: number | null;
};

// type DataShape = wpconvlib.Conversation;
interface DataShape {
  frac_neg : string
  obscene : string;
  threat : string;
  insult : string;
  identity_hate : string;
  rev_id: string;
  comment_text : string;
};

//
function makeScoreEnum(frac : number){
  return {
    notatall: (frac < 0.3) ? 1 : (frac < 0.5 ? 0 : -1),
    somewhat: (frac < 0.2) ? -0.5 : (frac < 0.8 ? 1 : -0.5),
    very: (frac < 0.5) ? -1 : (frac < 0.7 ? 0 : 1),
  }
}

class ArgError extends Error {}

function checkArguments(args: Params) : void {
  if (!fs.existsSync(args.file)) {
    throw new ArgError('--file argument does not exist: ' + args.file);
  }
  if(typeof(args.training_fraction) !== 'number') {
    throw new ArgError('--training_fraction must be a float, not: '
        + args.training_fraction);
  }
  if(!db_types.valid_id_regexp.test(args.question_group)) {
    throw new ArgError('--question_group must be a valid id-string (\w|_|-|.|:)+, not: '
        + args.question_group);
  }
  if(args.to_line !== null && args.to_line !== undefined
     && typeof(args.to_line) !== 'number') {
    throw new ArgError('--to_line must be a number, not: ' + args.to_line);
  }
  if(args.from_line !== null && args.from_line !== undefined
     && typeof(args.from_line) !== 'number') {
    throw new ArgError('--from_line must be a number, not: ' + args.from_line);
  }
}

function questionRowFromDatum(datum : DataShape,
    question_type : 'training' | 'test' | 'toanswer')
    : db_types.QuestionRow {
  let id = hashjs.sha256().update(datum.rev_id + ':' + datum.comment_text).digest('hex');
  let question : db_types.Question = { revision_id: id, revision_text: datum.comment_text } as any;

  let toxicity_scores = { enum: makeScoreEnum(parseFloat(datum.frac_neg)) };
  let readableAndInEnglishScores = {
    optional: true,
    enum: { yes: 1, no: -1 }
  };
  let obscene_scores = {
    optional: true,
    enum: makeScoreEnum(parseFloat(datum.obscene))
  };
  let hate_scores = {
    optional: true,
    enum: makeScoreEnum(parseFloat(datum.obscene))
  };
  let threat_scores = {
    optional: true,
    enum: makeScoreEnum(parseFloat(datum.obscene))
  };
  let insult_scores = {
    optional: true,
    enum: makeScoreEnum(parseFloat(datum.obscene))
  };

  let questionRow : db_types.QuestionRow = {
    accepted_answers: {
      readableAndInEnglish: readableAndInEnglishScores,
      toxic: toxicity_scores,
      obscene: obscene_scores,
      identityHate: hate_scores,
      threat: threat_scores,
      insult: insult_scores,
    },
    question: question,
    question_group_id: args.question_group,
    question_id: id,
    // TODO(ldixon): make nice typescript interence helper function.
    type: question_type,
  };
  return questionRow;
}

async function main(args : Params) {
  checkArguments(args);

  let spannerClient = spanner({ projectId: args.gcloud_project_id });
  let spannerInstance = spannerClient.instance(args.spanner_instance);
  let spannerDatabase = spannerInstance.database(args.spanner_db, { keepAlive: 5 });
  let db = new crowdsourcedb.CrowdsourceDB(spannerDatabase);
  let random = seedrandom(args.random_seed);

  // let fileAsString = fs.readFileSync(args.file, 'utf8');

  let total_added = 0;
  let training_added = 0;
  let test_added = 0;
  let batcher = new util.Batcher<db_types.QuestionRow>(async (batch : db_types.QuestionRow[]) => {
    if (args.action === 'update') {
      await db.updateQuestions(batch);
    } else if (args.action === 'insert') {
      await db.addQuestions(batch);
    } else if (args.action === 'print') {
      console.log(JSON.stringify(batch));
    } else if (args.action === 'count') {
    } else {
      throw new Error('invalid action: ' + args.action);
    }
    console.log(`questions in batch: ${batch.length}`);
    console.log(`total questions is now: ${total_added}`);
    total_added += batch.length;
  }, 10);

  await util.applyToLinesOfFile(args.file,
    async (line:string) => {
      let question_type : 'test' | 'training';
      if(random() >= args.training_fraction) {
        question_type = 'test';
        test_added += 1;
      } else {
        question_type = 'training';
        training_added += 1;
      }
      let question = questionRowFromDatum(JSON.parse(line), question_type);
      return batcher.add(question);
    }, { from_line: args.from_line, to_line: args.to_line });

  await batcher.flush();

  await db.close();

  console.log(`Completed. Added questions: ${total_added}`);
  console.log(`Training: ${training_added}`);
  console.log(`Test: ${test_added}`);
}

let args = yargs
    .option('file', {
        describe: 'Path to JSON file of questions to upload'
    })
    .option('random_seed', {
      describe: 'A random seed to be used to select fraction of comments to be used for training'
    })
    .option('training_fraction', {
      describe: 'Fraction of examples given to be for training'
    })
    .option('question_type', {
        describe: 'Question type, one of: training | test | toanswer'
    })
    .option('question_group', {
      describe: 'Question type, one of: training | test | toanswer'
    })
    .option('gcloud_project_id', {
      describe: 'Google Cloud Project Id'
    })
    .option('spanner_instance', {
      describe: 'Spanner instance name'
    })
    .option('spanner_db', {
      describe: 'Spanner database name'
    })
    .option('action', {
      describe: 'One of update | insert | print | count; default is print. '
    })
    .option('from_line', {
      describe: 'Start processing file at from_line (inclusive) [0,null]'
    })
    .option('to_line', {
      describe: 'Only process file until to_line (inclusive)'
    })
    .default('random_seed', 'I am a random seed string')
    .default('action', 'print')
    .default('gcloud_project_id', 'wikidetox')
    .default('spanner_instance', 'crowdsource')
    .default('spanner_db', 'testdb')
    .demandOption(['file', 'question_group', 'training_fraction'],
        'Please provide at least --file and --question_group, and --training_fraction.')
    .help()
    .argv;

main(args as any as Params)
  .then(() => {
    console.log('Success!');
  }).catch(e => {
    console.error('Failed: ', e);
  });