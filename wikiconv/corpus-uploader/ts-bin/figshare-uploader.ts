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

Setup:
  # Create and setup the config to access Figshare and the Google Cloud project
  mkdir -p ./config
  rsync -a --ignore_existing \
    ./figshare.template.config.ts ./config/figshare.config.ts
  # Appropriately edit: ./config/figshare.config.ts
  pico ./config/figshare.config.ts
  # Make sure we are authenticated with Google Cloud
  gcloud auth login

Usage:

  ts-node ./ts-bin/figshare-uploader.ts

Notes: Creates a local directory called 'tmp'.

*/

import * as shelljs from 'shelljs';
import * as config from '../config/config';
import axios from 'axios';
import * as request from 'request';
import { CloudStorageUtil } from './cloud_storage_util'
import { FigshareArticleListEntry, FigshareArticle, FigshareFileUploadStatus } from './figshare_types'
import * as util from './util';

// import * as path from 'path';

// modify BASE_URL, ACCESS_TOKEN, FILE_NAME and FILE_PATH according to your needs
const FIGSHARE_ARTILES_URL='https://api.figshare.com/v2'

import * as yargs from 'yargs';

// Command line arguments.
interface Params {
  language: string;
  article_id?: string;
  complete_file_id?: string;
}

// function check_langauge(language:string) {
//   let language_list_str = shelljs.exec(`gsutil ls gs://${figshare_config.CLOUD_URL}`,
//                                   {silent:true}).stdout as string;
//   let language_list = language_list_str.trim().split('\n')
//                         .map(p => path.basename(p));
//   if (language_list.indexOf(language) === -1) {
//     console.warn(`Languages at ${figshare_config.CLOUD_URL}`);
//     console.warn(JSON.stringify(language_list, null, 2));
//     console.error(`Error: The specified language '${language}' does not exist in the cloud URL at ${figshare_config.CLOUD_URL}`);
//     shelljs.exit(1);
//   }
// }

// shelljs.exec(`gsutil ls gs://${figshare_config.CLOUD_URL}/${args.language}`,
// {silent:true}).stdout as string;

async function main(args: Params) {
  shelljs.mkdir('-p', 'tmp')

  let gsutil = new CloudStorageUtil(config.GCLOUD_STORAGE_BUCKET)

  let figshare_api = axios.create({
    baseURL: FIGSHARE_ARTILES_URL,
    timeout: 1000 * 60 * 2, // two minute timeout.
    headers: {'Authorization': `token ${config.ACCESS_TOKEN}`}
  });

  let figshareArticles :FigshareArticleListEntry[] =
    (await figshare_api.get('/account/articles')).data;
  let articleTitleMap = util.mapBy(figshareArticles, f => f.title);

  let plans : config.FigshareArticleConfig[] = config.GCLOUD_STORAGE_PATH_TO_FIGSHARE_MAPPING;

  // For each langauge's plan, handle it.
  for(let plan of plans) {
    if (!(plan.figshare_article_name in articleTitleMap)) {
      throw new Error(`${plan.figshare_article_name} is missing from Figshare: creating new articles is not yet supported.`);
    }

    console.log(`Working on plan for: ${plan.figshare_article_name}`);

    // Get the filenames in cloud storage.
    let { subdirNames, fileNames } = await gsutil.ls(
      plan.cloud_storage_dir_path);

    let articleId = articleTitleMap[plan.figshare_article_name].id;
    console.log(`Getting article id: ${articleId}`);
    // get the article for that language.
    let fileshareArticle : FigshareArticle = (await figshare_api.get(
        `/account/articles/${articleId}`)).data;
    // console.log(`ArticleEntry: \n${JSON.stringify(fileshareArticle, null, 2)}`);
    console.log(`ArticleEntry: title: '${fileshareArticle.title}'; id: ${fileshareArticle.id}`);
    console.log(JSON.stringify(util.multiMapBy(fileshareArticle.files, (f) => f.status), null, 2));

    // Check each file
    for (let figshareFileEntryList of fileshareArticle.files) {
      console.log(`File status: ${figshareFileEntryList.status}`);
      if(figshareFileEntryList.status === 'available') {
        continue;
      }

      let fileUploadStatus : FigshareFileUploadStatus =
          (await figshare_api.get(figshareFileEntryList.upload_url)).data;
      console.log(figshareFileEntryList);

      let gloudPath = `${plan.cloud_storage_dir_path}/${figshareFileEntryList.name}`;
      let gcloud_file_size = await gsutil.size(gloudPath);

      console.log(`Gcloud: ${gloudPath}: ${gcloud_file_size}`);
      console.log(`Figshare: ${fileUploadStatus.name}: ${fileUploadStatus.size}`);

      console.log(`typeof(metadata.size): ${typeof(gcloud_file_size)}`);
      console.log(`typeof(fileUploadStatus.size): ${typeof(fileUploadStatus.size)}`);

      if(fileUploadStatus.size !== gcloud_file_size) {
        throw new Error(`Figshare and gcloud file size mismatch:
        Gcloud: ${gloudPath}: ${gcloud_file_size} bytes
        but on Figshare: ${fileUploadStatus.size} bytes
        `);
      }

      if(fileUploadStatus.status === 'PENDING') {
        console.log(`${fileUploadStatus.name} : PENDING => attempting to complete file upload.`)

        // Make the call to complete the file.
        for(let part of fileUploadStatus.parts) {
          if(part.status === 'COMPLETE') { continue; }
          console.log(part);
          console.log(`${fileUploadStatus.name} : partNo ${part.partNo} / ${fileUploadStatus.parts.length}:  PENDING => attempting to complete file part upload (${util.numberWithCommas(part.endOffset - part.startOffset)} of ${util.numberWithCommas(fileUploadStatus.size)} bytes).`)

          let fileStream = gsutil.readStream(gloudPath, {start: part.startOffset, end: part.endOffset });
          // await new Promise<void>((resolve, _reject) => { fileStream.on('readable', resolve) });
          // fileStream.on('readable', resolve) });

          await new Promise<{statusCode:number}>((resolve, reject) => {
            fileStream.pipe(
              request.put(`${figshareFileEntryList.upload_url}/${part.partNo}`)
                .on('error', reject)
                .on('end', resolve)
                .on('response', (response) => {
                  console.log(`Server initial responce: ${response.statusCode}: ${response.statusMessage}`);
                  // console.log(response);
                  if(response.statusCode !== 200) {
                    throw new Error(`Failed to complete file upload: /articles/${articleId}/files/${figshareFileEntryList.id}`);
                  }
                }));
            });
          console.log('Completed upload of part; updated status:');
          let filePartUploadStatus2 : FigshareFileUploadStatus =
            (await figshare_api.get(`${figshareFileEntryList.upload_url}/${part.partNo}`)).data;

          console.log(filePartUploadStatus2);
        }
      }

      let response = await figshare_api.post(`account/articles/${articleId}/files/${figshareFileEntryList.id}`);
      if(!(response.status >= 200 && response.status < 300)) {
        console.log(response);
        throw new Error(`Failed to complete file upload: account/articles/${articleId}/files/${figshareFileEntryList.id}`);
      }
      // shelljs.exit(1);
    }
  }
}

let args = yargs
  // .option('article_id', {
  //   describe: 'If specified, add-to/update an existing article'
  // })
  // .option('complete_file_id', {
  //   describe: 'If specified, the file id to complete'
  // })
  // .option('language', {
  //   describe: 'Uplaod dataset for this language'
  // })
  // .demandOption(
  //   ['language'],
  //   'The parameter --language is required.')
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
