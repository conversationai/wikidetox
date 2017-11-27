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

A small tool to download results of a spanner query and save it in a
local file it as jsonlines format (http://jsonlines.org/).

Usage:
  # Build
  yarn run build

  # Download and save 200 rows from Answers to download_test.json
  node build/server/setup/download_to_jsonlines.js \
    --gcloud_project_id=wikidetox \
    --spanner_instance=crowdsource \
    --spanner_db=testdb \
    --file="download_test.json" \
    --query="SELECT * FROM Answers LIMIT 200"

It can be handy to then updload the json file to bigquery, which you
can do with a command like this (assuming a database called 'crowd9'
exists):

bq --project=wikidetox --dataset_id=wikidetox:crowd9 \
  load --autodetect --source_format=NEWLINE_DELIMITED_JSON \
  crowd9.Answers ./Answers.json
*/

import * as yargs from 'yargs';
import * as fs from 'fs';
import * as spanner from '@google-cloud/spanner';

import * as db_types from '../db_types';

// Command line arguments.
interface Params {
  file:string,
  client_key_regexp:string,
  gcloud_project_id:string,
  spanner_instance:string,
  spanner_db:string,
  query: string,
  writeflags: string,
};

function appendData(fd : number, d : string) : Promise<void> {
  return new Promise((resolve, reject) => {
    fs.appendFile(fd, d, (err) => {
      if (err) return reject(err);
      resolve();
    });
  });
}

async function queryAndApply<T>(spannerDatabase: spanner.Database,
  query:string, f: (row:T) => Promise<void>) : Promise<void> {

  let streamingQuery:spanner.StreamingQuery = spannerDatabase.runStream({sql: query});

  let promiseQueue = Promise.resolve();

  let queueSize = 0;
  let resultCount = 0;

  let complete = new Promise<void>((resolve, reject) => {
    // Assumes that on('data') never happens after on('end').
    streamingQuery.on('data', (row) => {
      queueSize += 1;
      if (resultCount % 100 === 0) {
        console.log(`Next 100. (queueSize: ${queueSize}; resultCount: ${resultCount})`);
      }
      streamingQuery.pause();
      promiseQueue = promiseQueue.then(async () => {
        resultCount += 1;
        await f(row as any as T);
        queueSize -= 1;
        streamingQuery.resume();
        // return appendData(fd, `${JSON.stringify(row)}\n`);
      });
    });
    streamingQuery.on('error', (e) => { reject(e); });
    streamingQuery.on('end', () => {
      console.log(`Stream End. (queueSize: ${queueSize}; resultCount: ${resultCount})`);
      resolve(); });
  })

  await complete;
  await promiseQueue;
  console.log(`Completed stream. (${queueSize}; resultCount: ${resultCount})`);
}

async function main(args : Params) {
  console.log(`query: ${args.query}\n  to file: ${args.file}`);

  const fd : number = fs.openSync(args.file, args.writeflags);
  fs.writeFileSync(fd,'','utf8');

  let spannerClient = spanner({ projectId: args.gcloud_project_id });
  let spannerInstance = spannerClient.instance(args.spanner_instance);
  let spannerDatabase = spannerInstance.database(args.spanner_db, { keepAlive: 5 });

  await queryAndApply(spannerDatabase, args.query, (row) => {
    return appendData(fd, `${JSON.stringify(row)}\n`);
  }).catch(async (e) => { spannerDatabase.close(); throw e; });

  await new Promise((resolve, _reject) => spannerDatabase.close(resolve));
}

let args = yargs
    .option('file', {
        describe: 'Path to JSON file of questions to upload'
    })
    .option('query', {
      describe: 'SQL query to send.'
    })
    .option('writeflags', {
      describe: 'if `w`, overwrite the output file even if it already exists, ' +
        'wx` (default) for only writing if file does not exist. For more ' +
        'details see the flag descriptions at: ' +
        'https://nodejs.org/api/fs.html#fs_fs_open_path_flags_mode_callback '
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
    .default('writeflags', 'wx')
    .demandOption(['file', 'query', 'gcloud_project_id', 'spanner_instance', 'spanner_db'],
      'Please provide: --file, --query, --gcloud_project_id, --spanner_instance, --spanner_db')
    .help()
    .argv;

main(args as any as Params)
  .then(() => {
    console.log('Success!');
  }).catch(e => {
    console.error('Failed: ', e);
    process.exit(1);
  });