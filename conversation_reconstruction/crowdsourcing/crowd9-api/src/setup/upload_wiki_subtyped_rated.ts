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

// import * as http from 'http';
import * as yargs from 'yargs';
import * as fs from 'fs';
import * as spanner from '@google-cloud/spanner';

import * as db_types from '../db_types';
// import * as wpconvlib from '@conversationai/wpconvlib';
import * as crowdsourcedb from '../cs_db';
import {batchList} from './util'

/*
Usage:

  node build/server/setup/upload_wiki_subtyped_rated.js \
    --file="./tmp/subtypesdata/bad_test_x150.json" \
    --question_group="wp_x2000" \
    --question_type="test" \
    --update_only

  node build/server/setup/upload_wiki_subtyped_rated.js \
    --file="./tmp/subtypesdata/unsure_test_x150.json" \
    --question_group="wp_x2000" \
    --question_type="test" \
    --update_only

  node build/server/setup/upload_wiki_subtyped_rated.js \
    --file="./tmp/subtypesdata/good_test_x150.json" \
    --question_group="wp_x2000" \
    --question_type="test" \
    --update_only



  node build/server/setup/upload_wiki_subtyped_rated.js \
    --file="./src/setup/subtypesdata/bad_train_x50.json" \
    --question_group="wp_x2000" \
    --question_type="training" \
    --update_only

  node build/server/setup/upload_wiki_subtyped_rated.js \
    --file="./src/setup/subtypesdata/unsure_train_x50.json" \
    --question_group="wp_x2000" \
    --question_type="training" \
    --update_only

  node build/server/setup/upload_wiki_subtyped_rated.js \
    --file="./src/setup/subtypesdata/good_train_x50.json" \
    --question_group="wp_x2000" \
    --question_type="training" \
    --update_only

  node build/server/setup/upload_dataset.js \
    --file="./src/testdata/wp_badish_x1000.json" \
    --question_group="wp_x2000"
*/

// Command line arguments.
interface Params {
  file:string,
  question_type:string,
  question_group:string,
  gcloud_project_id:string,
  spanner_instance:string,
  spanner_db:string,
  update_only: boolean,
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

async function main(args : Params) {
  console.log(args.file);
  if (!fs.existsSync(args.file)) {
    console.error('--file argument does not exist: ' + args.file);
    return;
  }
  if(!db_types.valid_question_type_regexp.test(args.question_type)) {
    console.error('--question_type must be a valid question type (training|test|toanswer), not: '
        + args.question_type);
    return;
  }
  if(!db_types.valid_id_regexp.test(args.question_group)) {
    console.error('--question_type must be a valid question type (training|test|toanswer), not: '
        + args.question_type);
    return;
  }

  let spannerClient = spanner({ projectId: args.gcloud_project_id });
  let spannerInstance = spannerClient.instance(args.spanner_instance);
  let spannerDatabase = spannerInstance.database(args.spanner_db, { keepAlive: 5 });
  let db = new crowdsourcedb.CrowdsourceDB(spannerDatabase);

  let fileAsString = fs.readFileSync(args.file, 'utf8');
  let data : DataShape[] = JSON.parse(fileAsString);
  let questions : db_types.QuestionRow[] = [];
  for (let i = 0; i < data.length; i++) {
    let id = data[i].rev_id;
    let question : db_types.Question = {
      revision_id: id,
      revision_text: data[i].comment_text
    } as any;

    let toxicity_scores = { enum: makeScoreEnum(parseFloat(data[i].frac_neg)) };
    let readableAndInEnglishScores = {
      optional: true,
      enum: { yes: 1, no: -1 }
    };
    let obscene_scores = {
      optional: true,
      enum: makeScoreEnum(parseFloat(data[i].obscene))
    };
    let hate_scores = {
      optional: true,
      enum: makeScoreEnum(parseFloat(data[i].obscene))
    };
    let threat_scores = {
      optional: true,
      enum: makeScoreEnum(parseFloat(data[i].obscene))
    };
    let insult_scores = {
      optional: true,
      enum: makeScoreEnum(parseFloat(data[i].obscene))
    };

    questions.push({
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
      type: args.question_type as any,
    });
  }

  console.log(`conversations to add: ${data.length}`);
  console.log(`questions to add: ${questions.length}`);
  console.log(`(skipped bad conversations: ${data.length - questions.length})`);

  let batchedQuestions = batchList(10, questions);

  let total_added = 0;
  for(let batch of batchedQuestions) {
    if (args.update_only) {
      await db.updateQuestions(batch);
    } else {
      await db.addQuestions(batch);
    }
    total_added += batch.length;
    console.log(`uploaded questions: ${batch.length}`);
    console.log(`total of uploaded questions is now: ${total_added}`);
  }

  await db.close();
}

let args = yargs
    .option('file', {
        alias: 'f',
        describe: 'Path to JSON file of questions to upload'
    })
    .option('question_type', {
        alias: 't',
        describe: 'Question type, one of: training | test | toanswer'
    })
    .option('question_group', {
      alias: 'g',
      describe: 'Question type, one of: training | test | toanswer'
    })
    .option('gcloud_project_id', {
      alias: 'gcp',
      describe: 'Google Cloud Project Id'
    })
    .option('spanner_instance', {
      alias: 'i',
      describe: 'Spanner instance name'
    })
    .option('spanner_db', {
      alias: 's',
      describe: 'Spanner database name'
    })
    .option('update_only', {
      alias: 'u',
      describe: 'If true, then do an update instead of an insert of the questons.'
    })
    .default('update_only', false)
    .default('gcloud_project_id', 'wikidetox')
    .default('spanner_instance', 'crowdsource')
    .default('spanner_db', 'testdb')
    .demandOption(['file', 'question_group', 'question_type'],
        'Please provide at least --file and --question_group, and --question_type.')
    .help()
    .argv;

main(args as any as Params)
  .then(() => {
    console.log('Success!');
  }).catch(e => {
    console.error('Failed: ', e);
  });