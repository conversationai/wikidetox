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
        const sqlQuery =    `SELECT * 
                                FROM \`${this.projectId}.${this.datasetID}.${this.originalDataTable}\` `;
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

        this.table.insert(row)
            .then(() => {
                console.log(row);
            }).catch((err) => {
                console.log(JSON.stringify(err));
            });
    }

}
