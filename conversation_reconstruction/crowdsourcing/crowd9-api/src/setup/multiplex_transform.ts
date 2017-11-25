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

type ChunkFn = (chunk:string, encoding:string,
                pushFn :(streamName: string, chunk:string) => void) => void;


class MultiplexOutputStream {
  private queue :string[] = [];
  // full is true when writable has returned true;
  private full : boolean = false;
  // Must only be called when writable is not full (waiting for drain event).
  constructor (private writable: stream.Writable) {}

  tryPush(chunk: string) {
    if(this.full) {
      this.queue.push(chunk);
    } else {
      this.full = this.writable.write(chunk);
    }
  }

  // Should only be called after a drain event.
  public tryResume() {
    this.full = false;
    while (this.queue.length > 0 && !this.full) {
      const chunk = this.queue.pop()
      this.full = this.writable.write(chunk);
    }
  }

  public end(cb?:() => void) {
    this.writable.end(cb);
  }

  public isFull() { return this.isFull; }
}


// Safe multiplexing from input stream to many output streams.
// This class will pause and resume the input stream to this transform.
export class Multiplex extends stream.Transform {
  public outputStreams : { [streamName:string] : MultiplexOutputStream } = {};
  inputProcessor : ChunkFn = (chunk:string, encoding:string) => { return {}; };
  // defined only when closing.
  private completeCloseFn ?: () => void;
  constructor(options?:stream.TransformOptions) { super(options); }

  public setInputProcessor(f:ChunkFn) {
    this.inputProcessor = f;
  }

  // Only safe to call when not paused.
  maybeClose() {
    if(this.completeCloseFn !== undefined) {
      for (let streamName in this.outputStreams) {
        this.outputStreams[streamName].end(() => {
          delete this.outputStreams[streamName];
          if(this.completeCloseFn !== undefined &&
             Object.keys(this.outputStreams).length === 0) {
            this.completeCloseFn();
            delete this.completeCloseFn;
          }
        });
      }
    }
  }

  // Try to resume the input queue; returns true when all output queues not full,
  // i.e. that resume has succeeded.
  tryResume() : boolean {
    if(!this.isPaused()) {
      return false;
    }
    for (let streamName in this.outputStreams) {
      if(this.outputStreams[streamName].isFull()) {
        return false;
      }
    }
    this.resume();
    this.maybeClose();
    return true;
  }

  // Must only be called when writable is not full (waiting for drain event).
  addOutputStream(streamName: string, writable: stream.Writable ) {
    let multiplexOutput = new MultiplexOutputStream(writable);
    this.outputStreams[streamName] = multiplexOutput;
    writable.on('drain', () => {
      multiplexOutput.tryResume();
      this.tryResume();
    });
  }

  pushToQueue(streamName:string, chunk:string) {
    this.push(streamName);
    if(this.outputStreams[streamName].tryPush(chunk)) {
      this.pause();
    }
  }

  _transform(chunk:string, encoding:string, cb: (error :Error|null) => void) : void {
    this.inputProcessor(chunk, encoding, this.pushToQueue.bind(this));
    cb(null);
  }

  _flush(cb:() => void) : void {
    this.completeCloseFn = cb;
    // If we are paused, then an outputStream is full, so we wait for a drain event,
    // which will call this.maybeClose.
    if(!this.isPaused()) {
      this.maybeClose();
    }
  }
}