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

// Based on reading the cocde in:
// https://github.com/GoogleCloudPlatform/google-cloud-node/blob/master/packages/spanner/src/index.js
declare module '@google-cloud/spanner' {
  import * as stream from 'stream';
  namespace spanner {
    export interface Query {
      sql: string;
    }
    export interface SpannerDate {
      // A fake field to make this type unique: fake nominal typing using npm namespace.
      __type__: '@google-cloud/spanner:SpannerDate';
    }
    export interface SpannerFloat {
      // A fake field to make this type unique: fake nominal typing using npm namespace.
      __type__: '@google-cloud/spanner:SpannerFloat';
    }
    export interface SpannerInt {
      // A fake field to make this type unique: fake nominal typing using npm namespace.
      __type__: '@google-cloud/spanner:SpannerInt';
    }
    export interface SpannerTimestamp {
      // A fake field to make this type unique: fake nominal typing using npm namespace.
      __type__: '@google-cloud/spanner:SpannerTimestamp';
    }
    export interface SpannerBytes {
      // A fake field to make this type unique: fake nominal typing using npm namespace.
      __type__: '@google-cloud/spanner:SpannerBytes';
    }

    export type InputField = string | null | SpannerDate | SpannerFloat
                           | SpannerInt | SpannerTimestamp | SpannerBytes;
    export interface InputRow {
      [columnKey:string] : InputField;
    }
    export interface Table {
      insert(rows:InputRow[]): Promise<void>;
      deleteRows(rowKeys:string[] | string[][]) : Promise<void>;
      update(rows:InputRow[]) : Promise<void>;
    }

    // The value representation chosen here by the spanner nodejs client
    // library is pretty surprising: INT64s are converted into
    // Objects with a value field that is the string representation of the number.
    // Strings on the other hand are just strings.
    export type ResultField = string | { value: string } | null | Date;
    // Rows and Columns (Fields) in that row.
    export type ResultRow = { name:string; value: ResultField; }[]
    export type QueryResult = ResultRow[];
    type StreamingQuery = stream.Readable;
    // export interface StreamingQuery {
    //   on(kind:'error', f: (e:Error) => void) : void;
    //   on(kind:'data', f: (row:ResultRow) => void) : void;
    //   on(kind:'end', f: () => void) : void;
    // }

    export interface Database {
      table(tableName:string): Table;
      run(query:Query):Promise<QueryResult[]>;
      // runStream(query:Query): StreamingQuery;
      runStream(query:Query): stream.Readable;
      close(cb ?: () => void) : void;
    }
    export interface DatabaseOptions {
      keepAlive: number;  // number of minutes between pings to the DB.
    }
    export interface Instance {
      database(databaseName:string, opts ?: DatabaseOptions) : Database;
    }
    export interface Spanner {
      instance(instanceId:string): Instance;
    }
    // TODO(ldixon): define spanner date.
    export interface ListInstancesQuery {
      autoPaginate: boolean; // Default true
      filter: string; // Filter method to select instances
      maxApiCalls: number;
      pageSize: number;
      pageToken: string;
    }
    export interface ListInstancesResponse {
      err: Error;
      instances: Instance[];
      apiResponse: Object;
    }
    export interface Operation {}
    export interface SpannerInit {
      (params: { projectId: string }): Spanner;
      date(x: string | Date | null) : SpannerDate;
      timestamp(x: string | Date | null) : SpannerTimestamp;
      float(x: number | string | null) : SpannerFloat;
      int(x: number | string | null) : SpannerInt;
      bytes(x: number | string | null) : SpannerBytes;
      //
      createInstance(name: string, config : Object) : Promise<void>;
      // https://cloud.google.com/spanner/docs/reference/rpc/google.spanner.admin.instance.v1#google.spanner.admin.instance.v1.InstanceAdmin.ListInstances
      getInstances(query: ListInstancesQuery) : Promise<void>;
      operation(name:string): Operation;
    }
  }
  var spanner: spanner.SpannerInit;
  export = spanner;
}
