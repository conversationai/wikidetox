import * as csv_parse from "csv-parse";
import * as csv_stringify from "csv-stringify";
import * as yargs from 'yargs';
import * as fs from 'fs';
import * as stream from 'stream';

let stream_transform = require('stream-transform');

// Command line arguments.
interface Args {
  in_csv_file: string,
  out_json_file: string,
  out_csv_file: string,
};


async function outputToJson(inStream:stream.Transform, out_json_path:string) : Promise<void> {
  if (args.out_json_file) {
    let json_stringify : stream.Transform = stream_transform(
        (record : {conversations : {}}) : string => { return JSON.stringify(record.conversations) + '\n' });
    let out_file = fs.createWriteStream(out_json_path);
    let pipe = inStream.pipe(json_stringify).pipe(out_file);
    return new Promise<void>((resolve, _reject) => {
      pipe.on('close', resolve);
    });
  }
  return;
}

async function outputToCsv(inStream:stream.Transform, out_csv_path:string) : Promise<void> {
  if (args.out_csv_file) {
    let stringifier = csv_stringify({header:true,
        formatters: {
          conversations: function(value) { return JSON.stringify(value); }
        }
      });
    let out_file = fs.createWriteStream(out_csv_path);
    let pipe = inStream.pipe(stringifier).pipe(out_file);
    return new Promise<void>((resolve, _reject) => {
      pipe.on('close', resolve);
    });
  }
  return;
}

async function main(args:Args) : Promise<void> {
  let in_file = fs.createReadStream(args.in_csv_file);

  let parser = csv_parse({columns:true});

  let transformer : stream.Transform = stream_transform(
      (record : {[column:string]:string}) : { conversations: {} } => {
      let convs_obj = {
        conversation1: JSON.parse(record.conversation1),
        conversation2: JSON.parse(record.conversation2),
      };
      return { conversations: convs_obj };
  });

  let transformed = in_file.pipe(parser).pipe(transformer);
  let onceCsv = outputToCsv(transformed, args.out_csv_file);
  let onceJson = outputToJson(transformed, args.out_json_file);
  await onceCsv;
  await onceJson;
}


let args = yargs
  .option('in_csv_file', {
    describe: 'Path to input CSV file'
  })
  .option('out_json_file', {
    describe: 'Path to output json file'
  })
  .option('out_csv_file', {
    describe: 'Path to output json file'
  })
  .demandOption(['in_csv_file'], 'Please provide at least --in_csv_file.')
  .help()
  .argv;

main(args as any as Args)
  .then(() => {
    console.log('Success!');
  }).catch(e => {
    console.error('Failed: ', e);
  });