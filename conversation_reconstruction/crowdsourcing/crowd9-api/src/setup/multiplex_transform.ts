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

A multiplex transform class for handling cases when you want to
take a single input stream and send the output different places
depending on some aspect of the input chunk.

*/
import * as stream from 'stream';

type ChunkFn = (
  chunk:string, encoding:string,
  pushFn : (streamName: string,
            chunk:string,
            encoding?:string,
            callback?:() => void)
           => void)
  => void;

// Safe multiplexing from input stream to many output streams.
// This class will pause and resume the input stream to this transform.
export class Multiplex extends stream.Transform {
  public outputStreams : { [streamName:string] : stream.Writable } = {};
  public finishedPromises : { [streamName:string] : Promise<void> } = {};
  public fullStreams : { [streamName:string] : null } = {};
  private transformCb : ((error:Error|null) => void)[] = [];
  private completeCloseFn ?: () => void;
  private inputProcessor : ChunkFn = (chunk:string, encoding:string) => { return {}; };
  // defined only when closing.
  constructor(options?:stream.TransformOptions) { super(options); }

  public setInputProcessor(f:ChunkFn) {
    this.inputProcessor = f;
  }

  // Only safe to call when not paused.
  checkClose() {
    console.debug('checkClose');
    if(this.completeCloseFn !== undefined && Object.keys(this.fullStreams).length === 0) {
      let closeFn = this.completeCloseFn;
      console.debug('closing.');
      Promise.all(
        Object.keys(this.finishedPromises).map((streamName) => {
          this.outputStreams[streamName].end();
          return this.finishedPromises[streamName];
        }))
        .then(() => { closeFn(); console.debug('closed.'); })
        .catch((e) => {
          console.error(e.message);
        });
    }
  }

  // Try to resume the input queue; returns true when all output queues not full,
  // i.e. that resume has succeeded.
  checkResume() : void {
    console.debug('checkResume');
    if (this.transformCb !== undefined && Object.keys(this.fullStreams).length === 0) {
      for(let cb of this.transformCb) {
        cb(null);
      }
      this.transformCb = [];
      console.debug('resumed.');
    }
  }

  // Must only be called when writable is not full (waiting for drain event).
  addOutputStream(streamName: string, writable: stream.Writable ) {
    this.outputStreams[streamName] = writable;
    writable.on('drain', () => {
      console.debug('drain: ' + streamName);
      delete this.fullStreams[streamName];
      this.checkResume();
      this.checkClose()
    });
    writable.on('error', (e) => { console.error(`${streamName}: error:` + e.message); });
    writable.on('close', () => { console.debug(`${streamName}: close`); });
    this.finishedPromises[streamName] = new Promise((resolve, reject) => {
      writable.on('finish', () => { resolve(); console.debug(`${streamName}: finish`); });
    });
    writable.on('pipe', () => { console.debug(`${streamName}: pipe`); });
    writable.on('unpipe', () => { console.debug(`${streamName}: unpipe`); });
  }

  pushToQueue(streamName:string, chunk:Buffer|string|{}, encoding:string, cb:() => void) {
    this.push(streamName);
    let isNotFull = this.outputStreams[streamName].write(chunk, encoding, cb);
    if(!isNotFull) {
      this.fullStreams[streamName] = null;
    }
  }

  _transform(chunk:string, encoding:string, cb:(error:Error|null) => void) : void {
    this.inputProcessor(chunk, encoding, this.pushToQueue.bind(this));
    if (Object.keys(this.fullStreams).length === 0) {
      cb(null);
    } else {
      console.debug('full: adding transformCb');
      // Otherwise a drain event will be used to call transformCb.
      this.transformCb.push(cb);
    }
  }

  _flush(cb:(error?:Error, data?:Buffer|string|{}) => void) : void {
    console.debug('_flush');
    this.completeCloseFn = cb;
    this.checkClose();
  }
}