/*
Copyright 2018 Google Inc.

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
import * as spanner from '@google-cloud/spanner';
import * as runtime_types from './runtime_types';

// Spanner Row Representations in JS.
//
// Note: Cloud Spanner interprets Node.js numbers as FLOAT64s, so
// in the row format, they are treated as strings (spanner does
// the conversion to INT64s when appropriate)
// TODO (yiqingh): modify this part accordingly
export interface OutputRow {
  id: runtime_types.CommentId;
  ancestor_id: runtime_types.CommentId;
  authors: null | string[];
  cleaned_content: null | string;
  content: null | string;
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


interface SpannerFieldHandler<T> {
  field_name : string;
  fromSpannerResultField(row:spanner.ResultField) : T | null;
}

// TODO(ldixon): add fancier validation, more subtypes, e.g. for checking fields match specific T.
class JsonFieldHandler<T> implements SpannerFieldHandler<T> {
  constructor(public field_name: string) {
    this.field_name = field_name;
  }
  public fromSpannerResultField(field:spanner.ResultField) : T | null {
    if(field === null) {
      return null;
    }
    if(typeof(field) !== 'string') {
      console.log('Error: field:');
      console.dir(field);
      throw Error(`For ${this.field_name}: expected json field:string, not: ${typeof(field)}`);
    }
    return JSON.parse(field);
  }
}

// TODO(ldixon): add additional constraints, e.g. regexp matching.
class StringFieldHandler implements SpannerFieldHandler<string> {
  constructor(public field_name: string) {
    this.field_name = field_name;
  }
  public fromSpannerResultField(field:spanner.ResultField) : string | null {
    if(!(field === null || typeof(field) === 'string')) {
      console.log('Error: field:');
      console.dir(field);
      throw Error(`For ${this.field_name}: expected field:string, not: ${typeof(field)}`);
    }
    return field;
  }
}

class BytesFieldHandler implements SpannerFieldHandler<string> {
  constructor(public field_name: string) {
    this.field_name = field_name;
  }
  public fromSpannerResultField(field:spanner.ResultField) : string | null {
    if(!(field === null || typeof(field) === 'string')) {
      console.log('Error: field:');
      console.dir(field);
      throw Error(`For ${this.field_name}: expected field:string, not: ${typeof(field)}`);
    }
    return field;
  }
}

class IntFieldHandler implements SpannerFieldHandler<number> {
  constructor(public field_name: string) {
    this.field_name = field_name;
  }
  public fromSpannerResultField(field:spanner.ResultField) : number | null {
    if(typeof(field) === 'string') {
      throw Error(`For ${this.field_name}: expected field.value:string, but field:string`);
    } else if (field instanceof Date) {
      throw Error(`For ${this.field_name}: expected field.value:string, but field:Date`);
    } else if (field === null) {
      return null;
    }
    return parseInt(field.value);
  }
}

class FloatFieldHandler implements SpannerFieldHandler<number> {
  constructor(public field_name: string) {
    this.field_name = field_name;
  }
  public fromSpannerResultField(field:spanner.ResultField) : number | null {
    if(typeof(field) === 'string') {
      throw Error(`For ${this.field_name}: expected field.value:string, but field:string`);
    } else if (field instanceof Date) {
      throw Error(`For ${this.field_name}: expected field.value:string, but field:Date`);
    } else if (field === null) {
      return null;
    }
    return parseFloat(field.value);
  }
}

class TimestampFieldHandler implements SpannerFieldHandler<Date> {
  constructor(public field_name: string) {
    this.field_name = field_name;
  }
  public fromSpannerResultField(field:spanner.ResultField) : Date | null {
    if (!(field === null || field instanceof Date)) {
      throw Error(`For ${this.field_name}: expected field:Date, but field:${typeof(field)}`);
    }
    return field;
  }
}

interface HandlerSet { [field_name:string] : SpannerFieldHandler<any>; };

let handlers : SpannerFieldHandler<{}>[] = [
  new StringFieldHandler('id'),
  new StringFieldHandler('ancestor_id'),
  new JsonFieldHandler('authors'),
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

function addHandler(handlers : HandlerSet, handler : SpannerFieldHandler<{}>)
    : HandlerSet {
  handlers[handler.field_name] = handler;
  return handlers;
}
const handlerSet = handlers.reduce<HandlerSet>(addHandler, {});

export function parseOutputRows<T>(rows: spanner.ResultRow[]) : T {
  let output : { [field_name:string] : {} }[] = []
  for (let row of rows) {
    let ret: { [field_name:string] : {} } = {};
    for (let field of row) {
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
