// Extra typings
declare module 'csv-stringify' {
  import * as stream from 'stream';

  interface Options {
    header: boolean;
    formatters : { [columnName:string] : (x:any) => string };
  }
  let init_fn : (options:Options) => stream.Writable;
  export = init_fn;
}