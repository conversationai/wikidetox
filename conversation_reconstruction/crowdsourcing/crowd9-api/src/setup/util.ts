import * as linebyline from 'line-by-line';

export function batchList<T>(batchSize : number, list :T[]) : T[][] {
  let batches : T[][] = [];
  let batch : T[] = [];
  for(let x of list) {
    batch.push(x);
    if(batch.length >= batchSize) {
      batches.push(batch);
      batch = [];
    }
  }
  if(batch.length > 0) {
    batches.push(batch);
  }
  return batches;
}

export class Batcher<T> {
  public batch : T[] = [];
  constructor(public f:(batch:T[]) => Promise<void>,
              public batchSize: number) {}
  public async add(x:T) : Promise<void> {
    this.batch.push(x);
    if(this.batch.length >= this.batchSize) {
      await this.f(this.batch);
      this.batch = [];
    }
  }
  public async flush() : Promise<void> {
    if(this.batch.length > 0) {
      await this.f(this.batch);
    }
  }
}

// Apply an async function to each line, providing a promise
// for when all lines have been evaluated.
export async function applyToLinesOfFile(
    filename: string,
    f:(line:string) => Promise<void>,
    options?: {
      from_line ?: number | null;  // First line is line 1; match inclusive.
      to_line ?: number | null; // First line is line 1; match inclusive.
    }) {
  let lr = new linebyline(filename);
  let reading = true;
  //
  // A promise that is resolved when we get the next line.
  // This value is updated after reading each line to become
  // a new promise for the next line. This allows us to sync
  // actions to lines.
  let resolvefn = (line:string | null) => {};
  // Mutex to avoid double-calls of resolvefn
  let workingOnLine = false;
  let onceGetNextLine = new Promise<string | null>((resolve, reject) => {
    resolvefn = resolve;
    lr.on('line', (line) => { lr.pause(); workingOnLine = true; resolvefn(line); });
    lr.on('end', () => { reading = false; if(!workingOnLine) { resolvefn(null); } });
  });
  let linenumber = 0;
  while(reading) {
    linenumber++;
    let line = await onceGetNextLine;
    if(line === null) {
      break;
    }
    onceGetNextLine = new Promise<string | null>((resolve, reject) => {
      resolvefn = resolve;
    });
    if(options) {
      if (options.from_line && linenumber < options.from_line) {
        workingOnLine = false;
        lr.resume();
        continue;
      }
      if (options.to_line && linenumber > options.to_line) {
        break;
      }
    }
    await f(line);
    workingOnLine = false;
    lr.resume();
  }
}