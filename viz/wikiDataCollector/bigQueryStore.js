const BigQuery = require('@google-cloud/bigquery');
const async = require('async');

class BigQueryStore {

    constructor(config) {

        this.projectId = config.bigQuery.projectId;
        this.dataSetId = config.bigQuery.dataSetId;
        this.revisionsTable = config.bigQuery.revisionsTable;
        this.revertedTable = config.bigQuery.revertedTable;
        this.cronLogs = config.bigQuery.cronLogs;


        this.bigquery = BigQuery({
            projectId: this.projectId,
            keyFilename: config.gcloudKey
        });

    }

    validateSchema(row) {

        const schemaStructure = {
            timestamp: true,
            namespace: true,
            author: false,
            page: true,
            revision_text: true,
            attack: true,
            revision_id: true,
            // revert_id: true,
            sha1: true,
            page_id: true
        };

        let isInvalidValid = false;

        Object.keys(schemaStructure).forEach((field) => {
            if (row[field] === null || row[field] === '' || row[field] === undefined) {
                if (schemaStructure[field]) {
                    isInvalidValid = true;
                }
            }
        });

        return isInvalidValid;
    }

    addCommentData(rows, cb) {

        const dataset = this.bigquery.dataset(this.dataSetId);
        const table = dataset.table(this.revisionsTable);

        let invalidData = rows.filter((d) => this.validateSchema(d));
        if (invalidData.length) {
            cb('Invalid data : ', invalidData);
            return;
        }

        // Inserts data into a table
        table.insert(rows)
            .then((insertErrors, data) => {
                console.log(rows.length + ' rows inserted.');
                cb(null, rows.length + ' rows inserted.');
                return insertErrors;
            }).catch(function (err) {
                console.log(JSON.stringify(err));
                cb(err);
            });
    }

    makeQuery(query, cb) {
        const options = {
            query: query,
            useLegacySql: false // Use standard SQL syntax for queries.
        };
        let job;
        return this.bigquery
            .startQuery(options)
            .then((results) => {
                job = results[0];
                //console.log(`Job ${job.id} started.`);
                return job.promise();
            })
            .then(() => {
                //console.log(`Job ${job.id} completed.`);
                return job.getQueryResults();
            })
            .then((results) => {
                const rows = results[0];
                cb(null, rows)
            })
            .catch((err) => {
                console.error('ERROR:', err);
                cb(err)
            });
    }

    flagReverted(startNextJob) {

        // Query options list: https://cloud.google.com/bigquery/docs/reference/v2/jobs/query
        let that = this;
        const revertedQueries = {
            getAllRepeatedSha1s: () => {
                let t_Comments = this.dataSetId + '.' + this.revisionsTable,
                    t_Reverted = this.dataSetId + '.' + this.revertedTable;

                return `SELECT
                        t_comments.page_id AS page_id,
                        t_comments.sha1 AS sha1,
                            COUNT(*) AS count
                        FROM
                            ${t_Comments} as t_comments
                        LEFT JOIN
                             ${t_Reverted}  as t_reverted
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
                            count DESC`
            },
            getAllRowsWithSameSha1s: (pageId, sha1) => {
                let t_Comments = this.dataSetId + '.' + this.revisionsTable;

                return `SELECT page_id,sha1,timestamp FROM ${t_Comments}
                            WHERE  page_id='${pageId}' AND sha1='${sha1}'
                        ORDER BY timestamp ASC`;

            },
            // markAllEntriesAsRevertedBetween: (pageId, firstOccerence, lastOccerence) => {

            //     return `UPDATE toxic_comments_test.comments_test_copy SET is_reverted = true
            //                 WHERE page_id='${pageId}' AND
            //             timestamp >= '${firstOccerence}' AND timestamp < '${lastOccerence}'`;

            // },
            getAllRevertedRevisions: (pageId, firstOccerence, lastOccerence) => {
                let t_Comments = this.dataSetId + '.' + this.revisionsTable;

                if (firstOccerence === lastOccerence) {
                    return `SELECT timestamp,revision_id,revert_id FROM ${t_Comments} WHERE  page_id='${pageId}' AND
                        timestamp = '${firstOccerence}'`;
                }
                return `SELECT timestamp,revision_id,revert_id FROM ${t_Comments} WHERE  page_id='${pageId}' AND
                        timestamp >= '${firstOccerence}' AND timestamp < '${lastOccerence}'`;

            },
            addRevertedRevisions: (rows, cb) => {

                if (rows.length === 0) {
                    cb(null, []);
                    return;
                }

                let revertedRevisions = [],
                    revision_id = {};
                rows.forEach((row) => {
                    row.forEach((rev) => {
                        if (!revision_id[rev.revision_id]) {
                            revertedRevisions.push({
                                "timestamp": rev.timestamp.value,
                                "revision_id": String(rev.revision_id),
                                "revert_id": String(rev.revert_id)
                            });
                            revision_id[rev.revision_id] = true;
                        }
                    });
                });

                const dataset = this.bigquery.dataset(this.dataSetId);
                const table = dataset.table(this.revertedTable);

                // Inserts data into a table
                table.insert(revertedRevisions)
                    .then((insertErrors, data) => {
                        console.log(revertedRevisions.length + ' rows inserted.');
                        cb(null, revertedRevisions.length + ' rows inserted.');
                        return insertErrors;
                    }).catch(function (err) {
                        console.log(JSON.stringify(err));
                        cb(err);
                    });
            }

        };
        function getAllRepeatedSha1s(cb) {
            that.makeQuery(revertedQueries.getAllRepeatedSha1s(), function (err, rows) {
                if (!err) {
                    cb(null, rows)
                } else {
                    cb(err);
                }
            });
        }
        function getAllRowsWithSameSha1s(rows, cb) {
            console.log('Found ' + rows.length + ' repeated sha1 ....');
            if (rows.length === 0) {
                cb(null, []);
                return;
            }
            let queryListGetAllRowsWithSameSha1s = rows.map((row) => {
                let pageId = row.page_id,
                    sha1 = row.sha1;
                return revertedQueries.getAllRowsWithSameSha1s(pageId, sha1);
            });

            let queryFunctions = queryListGetAllRowsWithSameSha1s.map((query) => {
                return function (cb) {
                    that.makeQuery(query, function (err, rows) {
                        if (!err) {
                            let firstOccurrence = rows[0].timestamp.value,
                                lastOccurrence = rows[rows.length - 1].timestamp.value,
                                pageId = rows[0].page_id;
                            cb(null, { rowsLength: rows.length, firstOccurrence: firstOccurrence, lastOccurrence: lastOccurrence, pageId: pageId });
                        } else {
                            cb(err);
                        }
                    });
                }
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

            let queryList = list.map((row) => {
                return revertedQueries.getAllRevertedRevisions(row.pageId, row.firstOccurrence, row.lastOccurrence);
            });
            let queryFunctions = queryList.map((query) => {
                return function (cb) {
                    that.makeQuery(query, function (err, rows) {
                        if (!err) {
                            cb(null, rows);
                        } else {
                            cb(err);
                        }
                    });
                }
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
            revertedQueries.addRevertedRevisions
        ], function (err, result) {
            console.log('Done');
            startNextJob(true);
        })

    }

    logStreamTask(options) {


        const dataset = this.bigquery.dataset(this.dataSetId);
        const table = dataset.table(this.cronLogs);
        // Inserts data into a table
        table.insert([{
            "timestamp": options.timestamp,
            "cron_runtime": options.cron_runtime,
            "start_time": options.start_time,
            "end_time": options.end_time,
            "rows_added": options.rows_added
        }]).then((insertErrors, data) => {
            return insertErrors;
        }).catch(function (err) {
            console.log(JSON.stringify(err));
        });

    }

    getMonthData(start, end, send) {

        const t_Comments = this.dataSetId + '.' + this.revisionsTable;
        const t_Reveverted = this.dataSetId + '.' + this.revertedTable;

        const month_st = new Date(start).toISOString();
        const month_end = new Date(end).toISOString();

        const toxicLimit = 0.75;

        const getMonthsData = (cb) => {
            const query = `SELECT timestamp,revision_text, attack, author, page, revision_id FROM ${t_Comments}
                                 WHERE timestamp > '${month_st}' AND  timestamp < '${month_end}' AND attack >= ${toxicLimit}
                            ORDER BY timestamp ASC`;

            this.makeQuery(query, (err, d) => {
                cb(err, d)
            });

        }

        const getMonthsNonToxicCount = (cb) => {
            const query = ` SELECT count(revision_id) as count from ${t_Comments}
                            WHERE attack < ${toxicLimit} AND timestamp > '${month_st}' AND  timestamp < '${month_end}'`;

            this.makeQuery(query, (err, d) => {
                cb(err, d)
            });
        }

        const getRevertedData = (cb) => {
            const query = `SELECT t_reverted.revision_id as revision_id FROM ${t_Reveverted} as t_reverted
                                LEFT JOIN ${t_Comments} as t_scores ON t_scores.revision_id = t_reverted.revision_id
                            WHERE t_scores.timestamp > '${month_st}' AND  t_scores.timestamp < '${month_end}' AND t_scores.attack >= ${toxicLimit}
                            GROUP BY revision_id ORDER BY revision_id `;

            this.makeQuery(query, (err, d) => {
                cb(err, d)
            });
        }

        async.parallel([
            getMonthsData,
            getRevertedData,
            getMonthsNonToxicCount],
            function (err, result) {
                send(err, result);
            });
    }

    getCalendarData(send) {
        const t_Comments = this.dataSetId + '.' + this.revisionsTable;
        const t_Reveverted = this.dataSetId + '.' + this.revertedTable;

        const toxicLimit = 0.75;

        const getMonthsList = (cb) => {
            const query = `SELECT EXTRACT(month FROM timestamp) as month, EXTRACT(year FROM timestamp) as year , COUNT (revision_id) as total,
                        COUNT( CASE WHEN attack >= ${toxicLimit} THEN 1 END ) as toxic
                        FROM  ${t_Comments} GROUP BY month, year`;
            this.makeQuery(query, cb);
        }

        const getRevertedCount = (cb) => {
            const query = `SELECT EXTRACT(month FROM t_scores.timestamp) as month, EXTRACT(year FROM t_scores.timestamp) as year, count(t_reverted.revision_id) as count
                             FROM ${t_Reveverted} as t_reverted
                            RIGHT JOIN ${t_Comments} as t_scores ON t_scores.revision_id = t_reverted.revision_id WHERE t_scores.attack >= ${toxicLimit}
                            GROUP BY month, year`;
            this.makeQuery(query, cb);
        }

        async.parallel([
            getMonthsList,
            getRevertedCount],
            function (err, result) {
                send(err, result);
            });

    }

    //
}

module.exports = BigQueryStore;
