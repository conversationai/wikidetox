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
declare module '@google-cloud/bigquery' {
  namespace top_level {
    export interface QueryOptions {
      query: string;
      useLegacySql: boolean;
    }

    // The value representation chosen here by the spanner nodejs client
    // library is pretty surprising: INT64s are converted into
    // Objects with a value field that is the string representation of the number.
    // Strings on the other hand are just strings.
    export type ResultField = string | { value: string } | null | Date;
    // Rows and Columns (Fields) in that row.
    export type ResultRow = { name:string; value: ResultField; }[]
    export type QueryResult = {
      id: string;
      getMetadata() : { status: { errors : Error[] } };
    }
    export type QueryResults = ResultRow[];

    export interface Operation {}

    export interface BigQueryClient {
      new (params: { projectId: string }) : BigQueryClient;
      query(q:QueryOptions) : Promise<QueryResults>;
    }
  }
  var top_level: top_level.BigQueryClient;
  export = top_level;
}