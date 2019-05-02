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
            RockV6_1_TOXICITY, RockV6_1_FLIRTATION, RockV6_1_TOXICITY_THREAT, RockV6_1_TOXICITY_IDENTITY_HATE, RockV6_1_TOXICITY_INSULT, RockV6_1_SEXUALLY_EXPLICIT, RockV6_1_TOXICITY_OBSCENE, RockV6_1_SEVERE_TOXICITY,
            category1, sub_category1,
            category2, sub_category2,
            category3, sub_category3,
            page_id, page_title, id, 
            user_text, timestamp, 
            cleaned_content, type 
        FROM \`${this.table}\` 
        WHERE 
            timestamp BETWEEN TIMESTAMP('${monthStart}') AND TIMESTAMP('${monthEnd}')
            AND RockV6_1_TOXICITY > .8
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
                    AND RockV6_1_TOXICITY > .8
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
                    AND RockV6_1_TOXICITY > .8
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
