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
  namespace spanner {
    export interface Query {
      sql: string;
    }
    export interface SpannerDate {}
    export interface SpannerFloat {}
    export interface SpannerInt {}
    export interface SpannerTimestamp {}
    export interface InputRow {
      [columnKey:string] : string | null | SpannerDate | SpannerFloat
                         | SpannerInt | SpannerTimestamp
    }
    export interface Table {
      insert(rows:InputRow[]): Promise<void>;
      deleteRows(rowKeys:string[] | string[][]) : Promise<void>;
      update(rows:InputRow[]) : Promise<void>;
    }

    // Rows and Columns.
    export type ResultRow = {
      name:string,
      // The value representation chosen here by the spanner nodejs client
      // library is pretty surprising: INT64s are converted into
      // Objects with a value field that is the string representation of the number.
      // Strings on the other hand are just strings.
      value: string | { value: string } | null }[]
    export type QueryResult = ResultRow[];
    export interface Database {
      table(tableName:string): Table;
      run(query:Query):Promise<QueryResult[]>;
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