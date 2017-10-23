import * as csv_parse from "csv-parse";
import * as csv_stringify from "csv-stringify";
import * as yargs from 'yargs';
import * as fs from 'fs';
import * as stream from 'stream';

let stream_transform = require('stream-transform');

// Command line arguments.
interface Args {
  in_csv_file: string,
  golden: boolean,
  out_json_file: string,
  out_csv_file: string,
};

interface ResultData {
  conversations: {},
  _id ?: string,
  na_gold ?: string,
  now_toxic_gold ?: string,
  future_toxic_gold ?: string,
  na_gold_reason ?: string,
  now_toxic_gold_reason ?: string,
  future_toxic_gold_reason ?: string,
};

async function outputToJson(inStream:stream.Transform, out_json_path:string) : Promise<void> {
  if (args.out_json_file) {
    let json_stringify : stream.Transform = stream_transform(
        (record : ResultData) : string => { return JSON.stringify(record.conversations) + '\n' });
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

  let id = 0;

  let transformer : stream.Transform = stream_transform(
      (record : {[column:string]:string}) : ResultData => {
      let conv1 = JSON.parse(record.conversation1);
      let conv2 = JSON.parse(record.conversation2);
      let convs_obj = {
        conversation1: conv1,
        conversation2: conv2,
      };
      let result : ResultData = { conversations: convs_obj };
      if (args.golden && record.thebadconversation !== undefined) {
        id += 1;
        result._id = 'id_' + id;
        result.na_gold = 'false';
        result.na_gold_reason = '';
        result.now_toxic_gold = record.thebadconversation;
        result.now_toxic_gold_reason = '';
        result.future_toxic_gold = record.thebadconversation,
        result.future_toxic_gold_reason = '';
      }
      return result;
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
  .option('golden', {
    describe: 'Output golden fields.'
  })
  .option('out_json_file', {
    describe: 'Path to output json file'
  })
  .option('out_csv_file', {
    describe: 'Path to output json file'
  })
  .default('golden', false)
  .demandOption(['in_csv_file'], 'Please provide at least --in_csv_file.')
  .help()
  .argv;

main(args as any as Args)
  .then(() => {
    console.log('Success!');
  }).catch(e => {
    console.error('Failed: ', e);
  });