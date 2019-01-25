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
const BigQuery = require('@google-cloud/bigquery');

export class bigQueryData {
    private projectId: string;
    private datasetID: string;
    private originalDataTable: string;
    private distDataTable: string;
    
    private bigquery: any;
    private dataset: any;
    private table: any;

    constructor(config) {
        this.projectId = config.projectId;
        this.datasetID = config.datasetID;
        this.originalDataTable = config.originalDataTable;
        this.distDataTable = config.distDataTable;

        this.bigquery = new BigQuery({
            keyFilename: config.keyFilename,
            projectId: this.projectId,
        });

        this.dataset = this.bigquery.dataset(this.datasetID);
        this.table = this.dataset.table(this.distDataTable);
    }

    async querySourceTable() {

        // max page ID 57726837
        const sqlQuery =    `SELECT * 
                                FROM \`${this.projectId}.${this.datasetID}.${this.originalDataTable}\`
                            WHERE page_id >= 43295130`;
        console.log(`Query job started: ${sqlQuery}`);
      
        // Query options list: https://cloud.google.com/bigquery/docs/reference/v2/jobs/query
        const options = {
          query: sqlQuery,
          useLegacySql: false, // Use standard SQL syntax for queries.
        };
      
        // Runs the query
        const [rows] = await this.bigquery.query(options);
        console.log(`Got ${rows.length} rows`);
        return rows;
    }

    writeToTable(row, categories) {
        if (categories !== undefined) {
            for (let i = 0; i<=2; i++) {
                row[`category${i+1}`] = categories[i] ? categories[i].category : null;
                row[`sub_category${i+1}`] = categories[i] ? categories[i].subCategory : null;
                row[`subsub_category${i+1}`] = categories[i] ? categories[i].subsubCategory : null;
                row[`category${i+1}_confidence`] = categories[i] ? categories[i].confidence : null;
            }
        } else {
            for (let i = 0; i<=2; i++) {
                row[`category${i+1}`] = null;
                row[`sub_category${i+1}`] = null;
                row[`subsub_category${i+1}`] = null;
                row[`category${i+1}_confidence`] = null;
            }
        }

        // console.log(row);
        // return row.id

        this.table.insert(row)
            .then(() => {
                console.log(row);
            }).catch((err) => {
                console.log(JSON.stringify(err));
            });
    }

}
