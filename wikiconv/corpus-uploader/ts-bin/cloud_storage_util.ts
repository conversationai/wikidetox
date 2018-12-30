import * as storage from '@google-cloud/storage';
import {Observable, Observer} from 'rxjs';
import { Readable } from 'stream';
import { type } from 'os';

export interface LsResult { fileNames:string[], subdirNames: string[] };

export class CloudStorageUtil {
  instance = new storage.Storage();
  private bucket: storage.Bucket;

  constructor(bucketName: string) {
    this.bucket = this.instance.bucket(bucketName)
  }
  async ls(path:string) : Promise<LsResult> {
    return await new Promise<LsResult>((resolve, _reject) => {
      let subdirNames :string[] = [];
      let fileNames :string[] = [];
      let cb : storage.GetFilesCallback = (err, files, next, apires) => {
        // console.log(files);
        // console.log(apires);
        if (files) {
          fileNames = fileNames.concat(files.map(file => file.name));
        }
        if (apires) {
          // TODO: fix bad typings, and avoid any.
          subdirNames = subdirNames.concat((apires as any).prefixes)
        }
        if(!!next) {
          this.bucket.getFiles(next, cb);
        } else {
          resolve({fileNames: fileNames, subdirNames: subdirNames});
        }
      }
      this.bucket.getFiles({prefix: path, delimiter:'/', autoPaginate:false}, cb);
    });
  }

  // Returns a files size
  async size(filePath:string) : Promise<number> {
    const [metadata] = await this.bucket.file(filePath).getMetadata();
    return parseInt(metadata.size);
  }

  async readObs(filePath:string, options: storage.CreateReadStreamOptions)
  : Promise<Observable<string>> {
    // { start: start, end: end }
    return new Observable<string>((observer : Observer<string>) => {
      let stream = this.bucket.file(filePath).createReadStream(options);
        stream.on('error', observer.error)
        stream.on('response', observer.next)
        stream.on('end', observer.complete)
      // Any cleanup logic might go here
      return () => stream.destroy()
    });
  }

  async readStream(filePath:string, options: storage.CreateReadStreamOptions)
  : Promise<Readable> {
    // { start: start, end: end }
    return this.bucket.file(filePath).createReadStream(options);
  }
}
