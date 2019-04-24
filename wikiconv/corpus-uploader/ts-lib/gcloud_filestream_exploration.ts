/* Copyright 2018 Google Inc.
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
    http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License. */
/* ------------------------------------------------------------------------

Minimal example for downloading a file and showing how to count the file's
size.

Example usage:

ts-node ./ts-bin/gcloud_filestream_exploration.ts \
 --gcloud_bucket=wikidetox-wikiconv-public-dataset \
 --gcloud_file_path=dataset/Greek/wikiconv-el-20180701--00001-of-00004 \
 --end_offset=10240000 \
 --local_file_path=./tmp/foo
*/

import * as shelljs from 'shelljs';
import * as config from '../config/config';
import { CloudStorageUtil } from './cloud_storage_util'
import * as util from './util';
import * as fs from 'fs';
import * as yargs from 'yargs';

// Command line arguments.
interface Params {
  gcloud_bucket: string;
  gcloud_file_path: string;
  start_offset: number;
  end_offset?: number;
  local_file_path: string;
}

async function main(args: Params) {
  let gsutil = new CloudStorageUtil(config.GCLOUD_STORAGE_BUCKET)
  let type_is_logged = false;

  let fileStream = gsutil.readStream(args.gcloud_file_path,
      {start: 0, end: args.end_offset });
  let bytesDownloadedSoFar = 0;
  let chunksCount = 0;
  let chunksCountPrint = 0;
  let fileStreamCompleted = new Promise<void>((resolve,reject) => {
    fileStream.on('data', (chunk) => {
      if(!type_is_logged) {
        console.log(`chunks have type: ${typeof(chunk)}`);
        console.log(`chunk has length: ${chunk.length}`);
        console.log(`chunk has byte length: ${chunk.byteLength}`);
        type_is_logged = true;
      }
      if(chunksCount > chunksCountPrint) {
        console.log(`chunks so far: ${chunksCount}`)
        chunksCountPrint = chunksCount * 2;
      }
      bytesDownloadedSoFar += chunk.byteLength;
      chunksCount += 1;
    });
    fileStream.on('error', function(err) {
      console.error(err);
      reject(err);
    });
    fileStream.on('response', function(response) {
      console.log(`Server initial responce: ${response.statusCode}: ${response.statusMessage}`);
     });
     fileStream.on('end', function() {
      console.log('Download completed');
      console.log(`Final number of chunks: ${chunksCount}`);
      console.log(`Final number of bytes: ${bytesDownloadedSoFar}`);
      resolve();
    });
  });

  if(args.local_file_path) {
    fileStream.pipe(fs.createWriteStream(args.local_file_path));
  }
  await fileStreamCompleted;
}

let args = yargs
  .option('gcloud_bucket', {
    describe: 'Google cloud storage bucket name'
  })
  .option('gcloud_file_path', {
    describe: 'Path to a file on google cloud storage'
  })
  .option('local_file_path', {
    describe: 'Path to where to download file'
  })
  .option('start_offset', {
    default: 0,
    describe: 'Offset to where to start downloding file from (Default: 0)'
  })
  .option('end_offset', {
    describe: 'If specified, offset of last byte to download'
  })
  .demandOption(
    ['gcloud_bucket', 'gcloud_file_path'],
    'The parameters --gcloud_bucket and --gcloud_file_path are required')
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
