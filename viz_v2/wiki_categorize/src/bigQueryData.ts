const BigQuery = require('@google-cloud/bigquery');

export class bigQueryData {
    public projectId: string;
    public datasetID: string;
    public originalDataTable: string;
    public distDataTable: string;
    
    public bigquery: any;

    constructor(config) {
        this.projectId = config.projectId;
        this.datasetID = config.datasetID;
        this.originalDataTable = config.originalDataTable;
        this.distDataTable = config.distDataTable;

        this.bigquery = new BigQuery({
            keyFilename: config.keyFilename,
            projectId: this.projectId,
        });
    }

    async querySourceTable() {

        // The SQL query to run
        const sqlQuery =    `SELECT * 
                                FROM \`${this.projectId}.${this.datasetID}.${this.originalDataTable}\`
                            LIMIT 2234`;
                            // WHERE 
                            //     REGEXP_CONTAINS(page_title, r'Talk:')
                            // AND 
                            //     timestamp > TIMESTAMP("${dateStart}") 
                            // AND  
                            //     timestamp < TIMESTAMP("${dateEnd}")`;
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
        
        const dataset = this.bigquery.dataset(this.datasetID);
        const table = dataset.table(this.distDataTable);

        for (let i = 0; i<=2; i++) {
            row[`category${i+1}`] = categories[i] ? categories[i].category : null;
            row[`sub_category${i+1}`] = categories[i] ? categories[i].subCategory : null;
            row[`subsub_category${i+1}`] = categories[i] ? categories[i].subsubCategory : null;
            row[`category${i+1}_confidence`] = categories[i] ? categories[i].confidence : null;
        }

        // console.log(row);
        // return row.id

        table.insert(row)
            .then(() => {
                return row.id;
            }).catch((err) => {
                console.log(JSON.stringify(err));
            });
    }

}
