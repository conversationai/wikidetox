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
