
import * as BigQuery from "@google-cloud/bigquery";
import * as async from "async";

export class BigQueryStore {

    public projectId: string;
    public dataSetId: string;
    public revisionsTable: string;
    public revertedTable: string;
    public cronLogs: string;
    public bigquery: any;

    constructor(config) {

        this.projectId = config.bigQuery.projectId;
        this.dataSetId = config.bigQuery.dataSetId;
        this.revisionsTable = config.bigQuery.revisionsTable;
        this.revertedTable = config.bigQuery.revertedTable;
        this.cronLogs = config.bigQuery.cronLogs;

        this.bigquery = BigQuery({
            keyFilename: config.gcloudKey,
            projectId: this.projectId,
        });

    }

    public validateSchema(row) {

        const schemaStructure = {
            attack: true,
            author: false,
            namespace: true,
            page: true,
            page_id: true,
            // revision_text: true,
            revision_id: true,
            // revert_id: true,
            sha1: true,
            timestamp: true,
        };

        let isInvalidValid = false;

        Object.keys(schemaStructure).forEach((field) => {
            if (row[field] === null || row[field] === "" || row[field] === undefined) {
                if (schemaStructure[field]) {
                    isInvalidValid = true;
                }
            }
        });

        return isInvalidValid;
    }

    public addCommentData(rows, cb) {

        const dataset = this.bigquery.dataset(this.dataSetId);
        const table = dataset.table(this.revisionsTable);

        rows = rows.filter((d) => {
            if (this.validateSchema(d)) {
                console.log("Invalid data : ", d);
                return false;
            } else {
                return true;
            }
        });

        // Inserts data into a table
        table.insert(rows)
            .then((insertErrors, data) => {
                console.log(rows.length + " rows inserted.");
                cb(null, rows.length + " rows inserted.");
                return insertErrors;
            }).catch((err) => {
                console.log(JSON.stringify(err));
                cb(err);
            });
    }

    public makeQuery(query, cb) {
        const options = {
            query,
            useLegacySql: false, // Use standard SQL syntax for queries.
        };
        let job;
        return this.bigquery
            .startQuery(options)
            .then((results) => {
                job = results[0];
                // console.log(`Job ${job.id} started.`);
                return job.promise();
            })
            .then(() => {
                // console.log(`Job ${job.id} completed.`);
                return job.getQueryResults();
            })
            .then((results) => {
                const rows = results[0];
                cb(null, rows);
            })
            .catch((err) => {
                console.error("ERROR:", err);
                cb(err);
            });
    }

    public flagReverted(startNextJob) {

        // Query options list: https://cloud.google.com/bigquery/docs/reference/v2/jobs/query
        const that = this;
        const revertedQueries = {

            addRevertedRevisions: (rows, cb) => {

                if (rows.length === 0) {
                    cb(null, []);
                    return;
                }

                const revertedRevisions = [];
                const revisionId = {};
                rows.forEach((row) => {
                    row.forEach((rev) => {
                        if (!revisionId[rev.revision_id]) {
                            revertedRevisions.push({
                                revert_id: String(rev.revert_id),
                                revision_id: String(rev.revision_id),
                                timestamp: rev.timestamp.value,
                            });
                            revisionId[rev.revision_id] = true;
                        }
                    });
                });

                const dataset = this.bigquery.dataset(this.dataSetId);
                const table = dataset.table(this.revertedTable);

                // Inserts data into a table
                table.insert(revertedRevisions)
                    .then((insertErrors, data) => {
                        console.log(revertedRevisions.length + " rows inserted.");
                        cb(null, revertedRevisions.length + " rows inserted.");
                        return insertErrors;
                    }).catch((err) => {
                        console.log(JSON.stringify(err));
                        cb(err);
                    });
            },
            getAllRepeatedSha1s: () => {
                const tComments = this.dataSetId + "." + this.revisionsTable;
                const tReverted = this.dataSetId + "." + this.revertedTable;

                return `SELECT
                        t_comments.page_id AS page_id,
                        t_comments.sha1 AS sha1,
                            COUNT(*) AS count
                        FROM
                            ${tComments} as t_comments
                        LEFT JOIN
                             ${tReverted}  as t_reverted
                        ON
                            t_reverted.revision_id = t_comments.revision_id
                        WHERE
                            t_reverted.revision_id IS NULL
                        AND t_comments.revision_id IS NOT NULL
                        AND t_comments.sha1 IS NOT NULL
                            GROUP BY
                                sha1,
                                page_id
                        HAVING
                            COUNT(*) > 1
                        ORDER BY
                            count DESC`;
            },
            // markAllEntriesAsRevertedBetween: (pageId, firstOccerence, lastOccerence) => {

            //     return `UPDATE toxic_comments_test.comments_test_copy SET is_reverted = true
            //                 WHERE page_id='${pageId}' AND
            //             timestamp >= '${firstOccerence}' AND timestamp < '${lastOccerence}'`;

            // },
            getAllRevertedRevisions: (pageId, firstOccerence, lastOccerence) => {
                const tComments = this.dataSetId + "." + this.revisionsTable;

                if (firstOccerence === lastOccerence) {
                    return `SELECT timestamp,revision_id,revert_id FROM ${tComments} WHERE  page_id='${pageId}' AND
                        timestamp = '${firstOccerence}'`;
                }
                return `SELECT timestamp,revision_id,revert_id FROM ${tComments} WHERE  page_id='${pageId}' AND
                        timestamp >= '${firstOccerence}' AND timestamp < '${lastOccerence}'`;

            },
            getAllRowsWithSameSha1s: (pageId, sha1) => {
                const tComments = this.dataSetId + "." + this.revisionsTable;

                return `SELECT page_id,sha1,timestamp FROM ${tComments}
                            WHERE  page_id='${pageId}' AND sha1='${sha1}'
                        ORDER BY timestamp ASC`;

            },
        };
        function getAllRepeatedSha1s(cb) {
            that.makeQuery(revertedQueries.getAllRepeatedSha1s(), function (err, rows) {
                if (!err) {
                    cb(null, rows);
                } else {
                    cb(err);
                }
            });
        }
        function getAllRowsWithSameSha1s(shaRows, cb) {
            console.log("Found " + shaRows.length + " repeated sha1 ....");
            if (shaRows.length === 0) {
                cb(null, []);
                return;
            }
            const queryListGetAllRowsWithSameSha1s = shaRows.map((row) => {
                const pageId = row.page_id;
                const sha1 = row.sha1;
                return revertedQueries.getAllRowsWithSameSha1s(pageId, sha1);
            });

            const queryFunctions = queryListGetAllRowsWithSameSha1s.map((query) => {
                return (cbQueryFunctions) => {
                    that.makeQuery(query, (err, rows) => {
                        if (!err) {
                            const firstOccurrence = rows[0].timestamp.value;
                            const lastOccurrence = rows[rows.length - 1].timestamp.value;
                            const pageId = rows[0].page_id;
                            cbQueryFunctions(null, { rowsLength: rows.length, firstOccurrence, lastOccurrence, pageId });
                        } else {
                            cbQueryFunctions(err);
                        }
                    });
                };
            });

            async.parallelLimit(queryFunctions, 10, (err, results) => {
                if (err) {
                    cb(err);
                    return;
                }
                cb(null, results);
            });
        }

        function getAllReverted(list, cb) {
            if (list.length === 0) {
                cb(null, []);
            }

            const queryList = list.map((row) => {
                return revertedQueries.getAllRevertedRevisions(row.pageId, row.firstOccurrence, row.lastOccurrence);
            });
            const queryFunctions = queryList.map((query) => {
                return (cb) => {
                    that.makeQuery(query, (err, rows) => {
                        if (!err) {
                            cb(null, rows);
                        } else {
                            cb(err);
                        }
                    });
                };
            });

            async.series(queryFunctions, (err, results) => {
                if (err) {
                    cb(err);
                    return;
                }
                cb(null, results);
            });
        }

        async.waterfall([
            getAllRepeatedSha1s,
            getAllRowsWithSameSha1s,
            getAllReverted,
            revertedQueries.addRevertedRevisions,
        ], (err, result) => {
            console.log("Done");
            startNextJob(true);
        });

    }

    public logStreamTask(options) {

        const dataset = this.bigquery.dataset(this.dataSetId);
        const table = dataset.table(this.cronLogs);
        // Inserts data into a table
        table.insert([{
            timestamp: options.timestamp,
            cron_runtime: options.cron_runtime,
            start_time: options.start_time,
            end_time: options.end_time,
            rows_added: options.rows_added,
        }]).then((insertErrors, data) => {
            return insertErrors;
        }).catch((err) => {
            console.log(JSON.stringify(err));
        });

    }

    public getMonthData(start, end, send) {

        const tComments = this.dataSetId + "." + this.revisionsTable;
        const tReveverted = this.dataSetId + "." + this.revertedTable;

        const monthSt = new Date(start).toISOString();
        const monthEnd = new Date(end).toISOString();

        const toxicLimit = 0.75;

        const getMonthsData = (cb) => {
            const query = `SELECT timestamp,revision_text, attack, author, page, revision_id FROM ${tComments}
                                 WHERE timestamp > '${monthSt}' AND  timestamp < '${monthEnd}' AND attack >= ${toxicLimit}
                            ORDER BY timestamp ASC`;

            this.makeQuery(query, (err, d) => {
                cb(err, d);
            });

        };

        const getMonthsNonToxicCount = (cb) => {
            const query = ` SELECT count(revision_id) as count from ${tComments}
                            WHERE attack < ${toxicLimit} AND timestamp > '${monthSt}' AND  timestamp < '${monthEnd}'`;

            this.makeQuery(query, (err, d) => {
                cb(err, d);
            });
        };

        const getRevertedData = (cb) => {
            const query = `SELECT t_reverted.revision_id as revision_id FROM ${tReveverted} as t_reverted
                                LEFT JOIN ${tComments} as t_scores ON t_scores.revision_id = t_reverted.revision_id
                            WHERE t_scores.timestamp > '${monthSt}' AND  t_scores.timestamp < '${monthEnd}' AND t_scores.attack >= ${toxicLimit}
                            GROUP BY revision_id ORDER BY revision_id `;

            this.makeQuery(query, (err, d) => {
                cb(err, d);
            });
        };

        async.parallel([
            getMonthsData,
            getRevertedData,
            getMonthsNonToxicCount],
            (err, result) => {
                send(err, result);
            });
    }

    public getCalendarData(send) {
        const tComments = this.dataSetId + "." + this.revisionsTable;
        const tReveverted = this.dataSetId + "." + this.revertedTable;

        const toxicLimit = 0.75;

        const getMonthsList = (cb) => {
            const query = `SELECT EXTRACT(month FROM timestamp) as month, EXTRACT(year FROM timestamp) as year , COUNT (revision_id) as total,
                        COUNT( CASE WHEN attack >= ${toxicLimit} THEN 1 END ) as toxic
                        FROM  ${tComments} GROUP BY month, year`;
            this.makeQuery(query, cb);
        };

        const getRevertedCount = (cb) => {
            const query = `SELECT EXTRACT(month FROM t_scores.timestamp) as month, EXTRACT(year FROM t_scores.timestamp) as year,
                           count(t_reverted.revision_id) as count
                             FROM ${tReveverted} as t_reverted
                            RIGHT JOIN ${tComments} as t_scores ON t_scores.revision_id = t_reverted.revision_id WHERE t_scores.attack >= ${toxicLimit}
                            GROUP BY month, year`;
            this.makeQuery(query, cb);
        };

        async.parallel([
            getMonthsList,
            getRevertedCount],
            (err, result) => {
                send(err, result);
            });

    }
}
