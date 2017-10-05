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
import * as db_types from '../db_types';
import * as wpconvlib from 'wpconvlib';
import * as crowdsourcedb from '../crowdsourcedb';

/*
Usage:
  node build/server/setup/upload_dataset.js \
    --file="./src/testdata/conversations_job2_x5.json"
    --question_group="conversations_job2_x5"
*/

interface Params {
  file:string,
  question_type:string,
  question_group:string,
  gcloud_project_id:string,
  spanner_instance:string,
  spanner_db:string,
};

function main(args : Params) {
  console.log(args.file);
  if (!fs.existsSync(args.file)) {
    console.error('--file argument does not exist: ' + args.file);
    return;
  }
  if(!db_types.valid_question_type_regexp.test(args.question_type)) {
    console.error('--question_type must be a valid question type (training|test|toanswer), not: ' + args.type);
    return;
  }
  if(!db_types.valid_id_regexp.test(args.question_group)) {
    console.error('--question_type must be a valid question type (training|test|toanswer), not: ' + args.type);
    return;
  }

  let fileAsString = fs.readFileSync(args.file, 'utf8');
  let data : wpconvlib.Conversation[] = JSON.parse(fileAsString);
  let questions : db_types.QuestionRow[] = [];
  for (let i = 0; i < data.length; i++) {
    let question = JSON.stringify(data[i]);
    let structured_conv = wpconvlib.structureConversaton(data[i]);
    if(!structured_conv) {
      console.error('bad conversaion with no root: ' + question);
      break;
    }
    questions.push({
      accepted_answers: null,
      question: question,
      question_group_id: args.question_group,
      question_id: structured_conv.id + ':' + i,
      // TODO(ldixon): make nice typescript interence helper function.
      type: args.question_type as any,
    });
  }

  let db = new crowdsourcedb.CrowdsourceDB({
      cloudProjectId: args.gcloud_project_id,
      spannerInstanceId: args.spanner_instance,
      spannerDatabaseName: args.spanner_db
    });

  db.addQuestions(questions);

  console.log(`added questions: ${questions.length}`);
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
    .default('gcloud_project_id', 'wikidetox')
    .default('spanner_instance', 'crowdsource')
    .default('spanner_db', 'testdb')
    .default('question_type', 'toanswer')
    .demandOption(['file', 'question_group'], 'Please provide at least --file and --question_group.')
    .help()
    .argv;

main(args as any as Params);