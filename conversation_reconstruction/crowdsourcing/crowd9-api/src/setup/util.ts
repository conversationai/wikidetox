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
  constructor(public f:(batch:T[]) => Promise<void>, public batchSize: number) {}
  public async add(x:T) {
    this.batch.push(x);
    if(this.batch.length >= this.batchSize) {
      await this.f(this.batch);
      this.batch = [];
    }
  }
}