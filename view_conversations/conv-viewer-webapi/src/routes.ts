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
import * as bigquery from '@google-cloud/bigquery';
import * as express from 'express';

import * as config from './config';
import * as runtime_types from './runtime_types';
import * as httpcodes from './http-status-codes';

function convertToSimpleTypes(rows: bigquery.QueryResult) {
  // console.log(JSON.stringify(rows, null, 2));
  for(let r of rows) {
    for (let key in r) {
      let obj = r[key];
      if (obj === null || typeof(obj) === 'string' || typeof(obj) === 'number' ) {
        continue;
      }
      // if(obj) {
      //   console.log(`key: ${key} type: ${typeof(r[key])} constructor: ${obj.constructor.name}`);
      // } else {
      //   console.log(`skipping key: ${key} type: ${typeof(r[key])}.`);
      // }
      if (obj && obj.constructor.name === "BigQueryTimestamp" && 'value' in obj) {
        r[key] = obj.value;
      }
    }
  }
}

// TODO(ldixon): consider using passport auth
// for google cloud project.
export function setup(app : express.Express, conf : config.Config, bqClient : bigquery.BigQueryClient ) {

  app.get('/api/conversation-id/:conv_id', async (req, res) => {

    let conv_id : runtime_types.ConversationId =
      runtime_types.ConversationId.assert(req.params.conv_id);

    try {
      // TODO remove outer try wrapper unless it get used.
      const sqlQuery = `SELECT *
      FROM \`${conf.bigQueryProjectId}.${conf.bigQueryDataSetId}.${conf.bigQueryTable}\`
      WHERE conversation_id="${conv_id}"
      LIMIT 100`;
      // Query options list: https://cloud.google.com/bigquery/docs/reference/v2/jobs/query
      const options = {
        query: sqlQuery,
        useLegacySql: false, // Use standard SQL syntax for queries.
      };

      await bqClient
        .query(options)
        .then(results => {
          const rows = results[0];
          convertToSimpleTypes(rows);
          res.status(httpcodes.OK).send(JSON.stringify(rows, null, 2));
        });
    } catch(e) {
      console.error(`*** Failed: `, e);
      res.status(httpcodes.INTERNAL_SERVER_ERROR).send(JSON.stringify({ error: e.message }));
    }
  });

  app.get('/api/revision-id/:rev_id', async (req, res) => {
    let rev_id : runtime_types.RevisionId =
      runtime_types.RevisionId.assert(req.params.rev_id);

    try {
      // TODO remove outer try wrapper unless it get used.
      const sqlQuery = `SELECT *
      FROM \`${conf.bigQueryProjectId}.${conf.bigQueryDataSetId}.${conf.bigQueryTable}\`
      WHERE rev_id=${rev_id}
      LIMIT 100`;
      // Query options list: https://cloud.google.com/bigquery/docs/reference/v2/jobs/query
      const options = {
        query: sqlQuery,
        useLegacySql: false, // Use standard SQL syntax for queries.
      };

      await bqClient
        .query(options)
        .then(results => {
          const rows = results[0];
          convertToSimpleTypes(rows);
          res.status(httpcodes.OK).send(JSON.stringify(rows, null, 2));
        });
    } catch(e) {
      console.error(`*** Failed: `, e);
      res.status(httpcodes.INTERNAL_SERVER_ERROR).send(JSON.stringify({ error: e.message }));
    }
  });

  app.get('/api/page-id/:page_id', async (req, res) => {
    let page_id : runtime_types.PageId =
      runtime_types.PageId.assert(req.params.page_id);

    try {
      // TODO remove outer try wrapper unless it get used.
      const sqlQuery = `SELECT *
      FROM \`${conf.bigQueryProjectId}.${conf.bigQueryDataSetId}.${conf.bigQueryTable}\`
      WHERE page_id=${page_id}
      LIMIT 100`;
      // Query options list: https://cloud.google.com/bigquery/docs/reference/v2/jobs/query
      const options = {
        query: sqlQuery,
        useLegacySql: false, // Use standard SQL syntax for queries.
      };

      await bqClient
        .query(options)
        .then(results => {
          const rows = results[0];
          convertToSimpleTypes(rows);
          res.status(httpcodes.OK).send(JSON.stringify(rows, null, 2));
        });
    } catch(e) {
      console.error(`*** Failed: `, e);
      res.status(httpcodes.INTERNAL_SERVER_ERROR).send(JSON.stringify({ error: e.message }));
    }
  });

  app.get('/api/page-title/:page_title', async (req, res) => {
    let page_title : runtime_types.PageTitleSearch =
      runtime_types.PageTitleSearch.assert(req.params.page_title);

    try {
      // TODO remove outer try wrapper unless it get used.
      const sqlQuery = `SELECT *
      FROM \`${conf.bigQueryProjectId}.${conf.bigQueryDataSetId}.${conf.bigQueryTable}\`
      WHERE page_title LIKE "${page_title}"
      LIMIT 100`;
      // Query options list: https://cloud.google.com/bigquery/docs/reference/v2/jobs/query
      const options = {
        query: sqlQuery,
        useLegacySql: false, // Use standard SQL syntax for queries.
      };
      console.log(sqlQuery);

      await bqClient
        .query(options)
        .then(results => {
          const rows = results[0];
          convertToSimpleTypes(rows);
          res.status(httpcodes.OK).send(JSON.stringify(rows, null, 2));
        });
    } catch(e) {
      console.error(`*** Failed: `, e);
      res.status(httpcodes.INTERNAL_SERVER_ERROR).send(JSON.stringify({ error: e.message }));
    }
  });
}