/*
Copyright 2019 Google Inc.
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

const {BigQuery} = require('@google-cloud/bigquery');

interface queryConfig {
    gcloudKeyFilePath: string;
    bigQuery: {
        projectId: string;
        datasetID: string;
        dataTable: string;
    }
}

export class BigQueryData {
    private bigquery: any;
    private table: string;

    constructor(public config: queryConfig) {
        this.bigquery = new BigQuery({
            keyFilename: config.gcloudKeyFilePath,
            projectId: config.bigQuery.projectId,
        });
        this.table = `${config.bigQuery.projectId}.${config.bigQuery.datasetID}.${config.bigQuery.dataTable}`
    }

    public monthDataQuery (monthStart, monthEnd) {
        return `SELECT 
            RockV6_2_TOXICITY, RockV6_2_FLIRTATION, RockV6_2_THREAT, RockV6_2_IDENTITY_ATTACK, 
            RockV6_2_INSULT, RockV6_2_SEXUALLY_EXPLICIT, RockV6_2_PROFANITY, RockV6_2_SEVERE_TOXICITY, 
            category1, sub_category1,
            category2, sub_category2,
            category3, sub_category3,
            page_id, page_title, id, rev_id,
            user_text, timestamp, 
            content, cleaned_content, type
        FROM \`${this.table}\` 
        WHERE 
            timestamp BETWEEN TIMESTAMP('${monthStart}') AND TIMESTAMP('${monthEnd}')
            AND RockV6_2_TOXICITY > .8
        `;
    }

    public dailyTimelineQuery (monthStart, monthEnd) {
        return `SELECT day, sum(cd) 
                OVER (partition by day) as day_total
                FROM 
                    (SELECT date(timestamp) as day, count(distinct id) as cd 
                    FROM \`${this.table}\` 
                    WHERE 
                    timestamp BETWEEN TIMESTAMP('${monthStart}') AND TIMESTAMP('${monthEnd}')
                    AND RockV6_2_TOXICITY > .8
                    GROUP BY day )
                `;
    }

    public getMonthTimeline (datastart) {
        return ` WITH total AS (
                    SELECT 
                    DATE_TRUNC(DATE(timestamp), MONTH) as month, 
                    count(distinct id) as total_cd 
                    FROM  \`${this.table}\`
                    WHERE timestamp > TIMESTAMP('${datastart}')
                    AND type != 'DELETION'
                    GROUP BY month 
                ),
                tox AS (
                    SELECT 
                    DATE_TRUNC(DATE(timestamp), MONTH) as toxmonth, 
                    count(distinct id) as tox_cd 
                    FROM  \`${this.table}\`
                    WHERE timestamp > TIMESTAMP('${datastart}')
                    AND RockV6_2_TOXICITY > .8
                    AND type != 'DELETION'
                    GROUP BY toxmonth 
                )
                SELECT month, tox_cd / total_cd as share
                    FROM total
                    JOIN tox ON total.month = tox.toxmonth 
                    ORDER BY total.month DESC 
        `
    }

    public async queryTable(query: string): Promise<object> {
        const options = {
          query: query,
          useLegacySql: false, // Use standard SQL syntax for queries.
          timeoutMs: 10000
        };
        try {
            const [rows] = await this.bigquery.query(options);
            console.log(`Table query got ${rows.length} rows`)
            return rows;
        } catch(e) {
            console.log(e)
            return [];
        }
    }
}
