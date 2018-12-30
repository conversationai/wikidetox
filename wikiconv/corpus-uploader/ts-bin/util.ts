
export function mapBy<T>(xs:T[], keyFn:(x:T) => string) : { [key:string]:T } {
  let mapX: { [key:string]:T } = {};
  for(let x of xs) {
    let key = keyFn(x);
    if(key in mapX) {
      throw new Error(`Duplciate Key: ${key}`);
    }
    mapX[key] = x;
  }
  return mapX;
}

export function multiMapBy<T>(xs:T[], keyFn:(x:T) => string) : { [key:string]:T[] } {
  let mapX: { [key:string]:T[] } = {};
  for(let x of xs) {
    let key = keyFn(x);
    if(!(key in mapX)) { mapX[key] = []; }
    mapX[key].push(x);
  }
  return mapX;
}

export function numberWithCommas(x:number) :string {
  return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}
