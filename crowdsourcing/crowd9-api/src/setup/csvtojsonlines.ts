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

  ts-node src/setup/csvtojsonlines.ts \
    --infile="./tmp/foo.csv" \
    --outfile="./tmp/foo.json"
*/

import * as csvtojson from 'csvtojson';
import * as fs from 'fs';
import * as stream from 'stream';
import * as yargs from 'yargs';

// Command line arguments.
interface Params {
  infile: string, outfile: string,
}

async function main(args: Params) {
  let instream = fs.createReadStream(args.infile);
  let outstream = fs.createWriteStream(
      args.outfile, {flags: 'w', defaultEncoding: 'utf-8'});
  let csvToJson = csvtojson();

  let lineCount = 0;

  let onceDone = new Promise((resolve, reject) => {
    csvToJson.fromStream(instream)
        .on('json',
            (jsonObj: {}) => {
              lineCount++;
              outstream.write(`${JSON.stringify(jsonObj)}\n`);
            })
        .on('done', (error: Error) => {
          console.log(`lineCount: ${lineCount}`);
          outstream.end();
          if (error) {
            console.log('end error:' + error.message);
            reject(error);
          } else {
            console.log('end success.');
            resolve();
          }
        });
  });
  await onceDone;
}

let args = yargs.option('infile', {describe: 'Input path to CSV file.'})
               .option('outfile', {describe: 'Path to output JSON-lines to'})
               .demandOption(
                   ['infile', 'outfile'],
                   'Please provide at least --infile and --outfile.')
               .help()
               .argv;

main(args as any as Params)
    .then(() => {
      console.log('Success!');
    })
    .catch(e => {
      console.error('Failed: ', e);
      process.exit(1);
    });
