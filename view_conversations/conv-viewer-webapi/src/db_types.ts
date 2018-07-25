/*
 * Copyright 2018 Google Inc.
 *
 *Licensed under the Apache License, Version 2.0 (the "License");
 *you may not use this file except in compliance with the License.
 *You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 *Unless required by applicable law or agreed to in writing, software
 *distributed under the License is distributed on an "AS IS" BASIS,
 *WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *See the License for the specific language governing permissions and
 *limitations under the License.
*/

import * as spanner from '@google-cloud/spanner';
import * as ab2str from 'arraybuffer-to-string';
import * as runtime_types from './runtime_types';

// Spanner Row Representations in JS.
//
// Note: Cloud Spanner interprets Node.js numbers as FLOAT64s, so
// in the row format, they are treated as strings (spanner does
// the conversion to INT64s when appropriate)
export interface OutputRow {
  id: runtime_types.CommentId;
  ancestor_id: runtime_types.CommentId;
  authors: string[] | null;
  cleaned_content: string | null;
  content: string | null;
  conversation_id: runtime_types.ConversationId;
  indentation: number;
  page_id: number;
  page_title: string;
  parent_id: runtime_types.CommentId;
  replyTo_id: runtime_types.CommentId;
  rev_id: runtime_types.RevisionId;
  timestamp: Date | null;
  type: string;
  user_id: number | null;
  user_text: string | null;
}


abstract class SpannerFieldHandler<T> {
  public fieldName : string;
  constructor(public newFieldName: string) {this.fieldName = newFieldName}
  public abstract fromSpannerResultField(row:spanner.ResultField) : T | null;
}

// TODO(ldixon): add additional constraints, e.g. regexp matching.
class StringFieldHandler extends SpannerFieldHandler<string> {
  public fromSpannerResultField(field:spanner.ResultField) : string | null {
    if(!(field === null || typeof(field) === 'string')) {
      console.error('Error: field:');
      console.dir(field);
      throw Error(`For ${this.fieldName}: expected field:string, not: ${typeof(field)}`);
    }
    return field;
  }
}

class BytesFieldHandler extends SpannerFieldHandler<string> {
  public fromSpannerResultField(field:spanner.ResultField) : string | null {
    if (field === null){
      return null;
    }
    if(!(field instanceof Uint8Array)) {
        console.error('Error: field:');
        console.dir(field);
        throw Error(`For ${this.fieldName}: expected field: byte array, not: ${typeof(field)}`);
    }
    return ab2str(field as Uint8Array);
  }
}

class ArrayFieldHandler extends SpannerFieldHandler<string[]> {
  public fromSpannerResultField(field:spanner.ResultField) : string[] | null {
    if (field === null) {
      return field;
    }
    if (!(field instanceof Array)) {
      console.error('Error: field:');
      console.dir(field);
      throw Error(`For ${this.fieldName}: expected field: string array, not: ${typeof(field)}`);
    }
    return field as string[];
  }
}



class IntFieldHandler extends SpannerFieldHandler<number> {
  public fromSpannerResultField(field:spanner.ResultField) : number | null {
    if(typeof(field) === 'string') {
      throw Error(`For ${this.fieldName}: expected field.value:string, but field:string`);
    } else if (field instanceof Date) {
      throw Error(`For ${this.fieldName}: expected field.value:string, but field:Date`);
    } else if (field === null) {
      return null;
    }
    return parseInt((field as spanner.ResultValue).value, 10);
  }
}

class FloatFieldHandler extends SpannerFieldHandler<number> {
  public fromSpannerResultField(field:spanner.ResultField) : number | null {
    if(typeof(field) === 'string') {
      throw Error(`For ${this.fieldName}: expected field.value:string, but field:string`);
    } else if (field instanceof Date) {
      throw Error(`For ${this.fieldName}: expected field.value:string, but field:Date`);
    } else if (field === null) {
      return null;
    }
    return parseFloat((field as spanner.ResultValue).value);
  }
}

class TimestampFieldHandler extends SpannerFieldHandler<Date> {
  public fromSpannerResultField(field:spanner.ResultField) : Date | null {
    if (!(field === null || field instanceof Date)) {
      throw Error(`For ${this.fieldName}: expected field:Date, but field:${typeof(field)}`);
    }
    return field;
  }
}

interface HandlerSet { [fieldName:string] : SpannerFieldHandler<Date | number | string | string[]>; };
interface ParsedOutput { [fieldName:string] : string | string[] | Date | number | null; };

const handlers : Array<SpannerFieldHandler<Date | number | string | string[]>> = [
  new StringFieldHandler('id'),
  new StringFieldHandler('ancestor_id'),
  new ArrayFieldHandler('authors'),
  new BytesFieldHandler('cleaned_content'),
  new BytesFieldHandler('content'),
  new StringFieldHandler('conversation_id'),
  new IntFieldHandler('indentation'),
  new IntFieldHandler('page_id'),
  new StringFieldHandler('page_title'),
  new StringFieldHandler('parent_id'),
  new StringFieldHandler('replyTo_id'),
  new IntFieldHandler('rev_id'),
  new TimestampFieldHandler('timestamp'),
  new StringFieldHandler('type'),
  new IntFieldHandler('user_id'),
  new StringFieldHandler('user_text'),
];

function addHandler(inputHandlers : HandlerSet, handler : SpannerFieldHandler<Date | number | string | string[]>)
    : HandlerSet {
  inputHandlers[handler.fieldName] = handler;
  return inputHandlers;
}
const handlerSet = handlers.reduce<HandlerSet>(addHandler, {});

export function parseOutputRows<T>(rows: spanner.ResultRow[]) : T {
  const output : ParsedOutput[] = []
  for (const row of rows) {
    const ret:  { [fieldName:string] : string | string[] | Date | number | null } = {};
    for (const field of row) {
      if(!(field.name in handlerSet)) {
        console.error(`Field ${field.name} does not have a handler and so cannot be interpreted.`);
        break;
      }
      ret[field.name] = handlerSet[field.name].fromSpannerResultField(field.value);
    }
    output.push(ret)
  }
  return output as any as T;
}
