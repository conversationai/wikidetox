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

*/

import * as shelljs from 'shelljs';
import * as config from '../config/config';
import axios from 'axios';
import { AxiosInstance } from 'axios';
import * as request from 'request';
import { CloudStorageUtil } from '../ts-lib/cloud_storage_util';
import * as figshare from '../ts-lib/figshare_types';
import * as util from '../ts-lib/util';

const FIGSHARE_ARTILES_URL='https://api.figshare.com/v2'

import * as yargs from 'yargs';

interface ConurrentUploadStatus { [upload_url_with_part:string] : {
  uploaded: number;
  size: number;
  filename: string,
  onceComplete ?: Promise<void>
} };

// Command line arguments.
interface Params {
  conurrency: number;
}

class FilePlanStatus {
  // Status of the file being uploaded. Only created after the init all.
  fileUploadStatus : figshare.FileUploadStatus;

  public get cloudPath() {
    return `${this.plan.cloud_storage_dir_path}/${this.fileListEntry.name}`
  }

  constructor(
      private gsutil: CloudStorageUtil,
      private figshare_api: AxiosInstance,
      // Config for the article that this is being uploaded to.
      public plan: config.FigshareArticleConfig,
      // The file entry being uploaded.
      // Note: fileListEntry.name matches the cloud file name
      public fileListEntry:figshare.FileListEntry) {
  }

  public async initStatus() : Promise<figshare.FileUploadStatus> {
    this.fileUploadStatus =
      (await this.figshare_api.get(this.fileListEntry.upload_url)).data;
    console.log(this.fileListEntry);
    let gcloud_file_size = await this.gsutil.size(this.cloudPath);

    if(this.fileUploadStatus.size !== gcloud_file_size) {
      // TODO: maybe check hashes is they exist in figshare yet?
      console.log(`Gcloud: ${this.cloudPath}: ${gcloud_file_size}`);
      console.log(`Figshare: ${this.fileUploadStatus.name}: ${this.fileUploadStatus.size}`);

      console.log(`typeof(metadata.size): ${typeof(gcloud_file_size)}`);
      console.log(`typeof(fileUploadStatus.size): ${typeof(this.fileUploadStatus.size)}`);

      throw new Error(`Figshare and gcloud file size mismatch:
      Gcloud: ${this.cloudPath}: ${gcloud_file_size} bytes
      but on Figshare: ${this.fileUploadStatus.size} bytes
      `);
    }

    return this.fileUploadStatus;
  }


  public async uploadFileParts(
    concurrent_part_uploads: ConurrentUploadStatus,){
    console.log(`${this.fileListEntry.name} : PENDING => attempting to complete file upload.`)

    // Make the call to complete the file.
    for(let part of this.fileUploadStatus.parts) {
      console.log('concurrent_part_uploads:');
      console.log(JSON.stringify(concurrent_part_uploads, null, 2));

      while(Object.keys(concurrent_part_uploads).length >= args.conurrency) {
        await util.sleep(500);
        console.log('concurrent_part_uploads:');
        console.log(JSON.stringify(concurrent_part_uploads, null, 2));
      }

      if(part.status === 'COMPLETE') { continue; }
      console.log(part);
      console.log(`${this.fileUploadStatus.name} : partNo ${part.partNo} / ${this.fileUploadStatus.parts.length}:  PENDING => attempting to complete file part upload (${util.numberWithCommas(part.endOffset - part.startOffset)} of ${util.numberWithCommas(this.fileUploadStatus.size)} bytes).`)

      let fileStream = this.gsutil.readStream(this.cloudPath, {start: part.startOffset, end: part.endOffset });

      let fullUploadPath = `${this.fileListEntry.upload_url}/${part.partNo}`;
      concurrent_part_uploads[fullUploadPath] = {
        filename: this.fileListEntry.name,
        uploaded: 0,
        size: part.endOffset - part.startOffset,
        onceComplete: undefined
      };
      fileStream.on('data', (chunk) => {
        concurrent_part_uploads[fullUploadPath].uploaded += chunk.length;
      })
      concurrent_part_uploads[fullUploadPath].onceComplete = new Promise<void>(
        (resolve, reject) => {
          fileStream.pipe(
            request.put(fullUploadPath)
              .on('error', reject)
              .on('end', () => {
                delete concurrent_part_uploads[fullUploadPath];
                resolve();
              })
              .on('response', (response) => {
                console.log(`Server initial responce: ${response.statusCode}: ${response.statusMessage}`);

                if(response.statusCode !== 200) {
                  throw new Error(`Failed to complete file upload: ${this.fileListEntry.name}`);
                }
              }));
          });

      console.log('Completed upload of part; updated status:');
      let filePartUploadStatus2 : figshare.FileUploadStatus =
        (await this.figshare_api.get(fullUploadPath)).data;

      console.log(filePartUploadStatus2);
    }
  }
}

async function main(args: Params) {
  let gsutil = new CloudStorageUtil(config.GCLOUD_STORAGE_BUCKET)

  let figshare_api = axios.create({
    baseURL: FIGSHARE_ARTILES_URL,
    timeout: 1000 * 60 * 2, // two minute timeout.
    headers: {'Authorization': `token ${config.ACCESS_TOKEN}`}
  });

  let concurrent_part_uploads: ConurrentUploadStatus = {};

  let figshareArticles :figshare.ArticleListEntry[] =
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
    let fileshareArticle : figshare.Article = (await figshare_api.get(
        `/account/articles/${articleId}`)).data;
    // console.log(`ArticleEntry: \n${JSON.stringify(fileshareArticle, null, 2)}`);
    console.log(`ArticleEntry: title: '${fileshareArticle.title}'; id: ${fileshareArticle.id}`);
    console.log(JSON.stringify(util.multiMapBy(fileshareArticle.files, (f) => f.status), null, 2));

    let filesByName = util.mapBy(fileshareArticle.files, (f) => f.name);
    let missingNames = fileNames.filter((n) => n in filesByName)
    if (missingNames.length > 0) {
      throw Error(`Missing files on figshare: ${JSON.stringify(missingNames)}`);
    }

    // Check each file
    for (let figshareFileListEntry of
        fileshareArticle.files.sort((f1,f2) => f1.name.localeCompare(f2.name))) {
      console.log(`File status: ${figshareFileListEntry.status}`);
      if(figshareFileListEntry.status === 'available') {
        continue;
      }

      let planStatus: FilePlanStatus = new FilePlanStatus(
        gsutil, figshare_api, plan, figshareFileListEntry);
      await planStatus.initStatus();

      if(planStatus.fileUploadStatus.status === 'PENDING') {
        await planStatus.uploadFileParts(concurrent_part_uploads);
      }

      while(Object.keys(concurrent_part_uploads).length !== 0) {
        console.log('waiting for concurrent_part_uploads for this file:');
        console.log(JSON.stringify(concurrent_part_uploads, null, 2));
        await util.sleep(200);
      }

      let fileUploadStatus2 : figshare.FileUploadStatus = (await figshare_api.get(`account/articles/${articleId}/files/${figshareFileListEntry.id}`)).data;
        console.log(fileUploadStatus2);
      while(fileUploadStatus2.status !== 'COMPLETE') {
        console.log(`Attempting to complete file upload...`)
        let response = await figshare_api.post(`account/articles/${articleId}/files/${figshareFileListEntry.id}`);
        if(!(response.status >= 200 && response.status < 300)) {
          console.error(`Failed to complete file upload for ${figshareFileListEntry.name}: ${response.status}: ${response.statusText}\n retrying...`);
        }
        let figshareFileEntryList2 = (await figshare_api.get(`account/articles/${articleId}/files/${figshareFileListEntry.id}`)).data;
      }
      // shelljs.exit(1);
    }
  }
}

let args = yargs
  .option('concurrency', {
    default: 5,
    type: 'number',
    describe: 'If specified, number of concurrent parts to upload'
  })
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
