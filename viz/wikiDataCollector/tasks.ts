#!/usr/bin/env node
// jshint esnext:true

import * as async from "async";
import * as program from "commander";
import * as fs from "fs";

import { BigQueryStore } from "./BigQueryStore";
import { GetToxicScore } from "./getToxicScore";
import { GetWikiData } from "./getWikiData";
import { StoreData } from "./StoreData";
import { TestCommentData } from "./testCommentData";

// TODO : pass this as params
const configPath = "config/production.json";
const config = JSON.parse(fs.readFileSync(configPath, "utf8"));

const wikidata = new GetWikiData();
const toxicScore = new GetToxicScore(config);
const testCommentData = new TestCommentData(config);
const bigquery = new BigQueryStore(config);

// local store
const storeData = new StoreData("/data");

const streamData = {
    addCommentForRevidData: (data, cb) => {
        wikidata.addCommentForRevidData(data, (err, dataRevid) => {
            if (err) {
                cb(err);
            } else {
                cb(null, dataRevid);
            }
        });
    },
    addDataToBigQueryStore: (data, cb) => {
        bigquery.addCommentData(data, (err, info) => {
            if (err) {
                console.log(err, info);
            } else {
                cb(null, info);
            }
        });
    },
    addToxicScore: (data, cb) => {
        toxicScore.addToxicScore(data, (err, dataScore) => {
            if (err) {
                console.log(err, dataScore);
            } else {
                cb(null, dataScore);
            }
        });
    },
    getRecentChanges: (start, end, cb) => {
        wikidata.getRecentChanges(start, end, (err, data) => {
            if (err) {
                cb(err);
            } else {
                cb(null, data);
            }
        });
    },
};

const doStreaming = (start, end, cb) => {
    const t0 = new Date().getTime();
    async.waterfall([
        (cb) => {
            streamData.getRecentChanges(start, end, cb);
        },
        (data, cb) => {
            streamData.addCommentForRevidData(data, cb);
        },
        (data, cb) => {
            streamData.addToxicScore(data, cb);
        },
        (data, cb) => {
            streamData.addDataToBigQueryStore(data, cb);
        },
    ], (err, result) => {

        if (err) {
            cb(err);
        }
        cb(null, {
            result,
            timeTook: (new Date().getTime() - t0) / 1000 + "s",
        });
        console.log("Call took " + (new Date().getTime() - t0) / 1000 + " seconds.");
    });
};

const getMonthData = (start, end, cb) => {
    bigquery.getMonthData(start, end, cb);
};

export class Tasks {

    public doStreaming = doStreaming;
    public flagReverted = bigquery.flagReverted.bind(bigquery);
    public logStreamTask = bigquery.logStreamTask.bind(bigquery);
    public getMonthData = bigquery.getMonthData.bind(bigquery);
    public getCalendarData = bigquery.getCalendarData.bind(bigquery);
}

/* CMD line interface for testing */

program
    .version("0.0.1")
    .command("streamData <start_time> <end_time>")
    .description("Collect, score and add data to BigQuery table.")
    .action((start, end) => {
        doStreaming(start, end, (err, data) => {
            if (err) {
                console.log("Error : ", err);
                return;
            }
            console.log(data);
        });
    });

program
    .version("0.0.1")
    .command("flagRevert")
    .description("Mark reverted commits")
    .action((start, end) => {
        bigquery.flagReverted(() => { console.log("Done"); });
    });

program
    .command("addComments <filePath>")
    .description("Find revids for the given file and add comments to it.")
    .action((filePath) => {
        const t0 = new Date().getTime();
        storeData.readFile(filePath, (data) => {

            if (typeof data === "string") {
                data = JSON.parse(data);
            }
            data.forEach((r) => { r.revid = r.rev_id; });
            console.log(data.length);

            function storeInter(dataInter, i) {
                const fileName = filePath.replace(".json", "");

                storeData.createFolder(fileName);
                storeData.clearFolder(fileName);

                storeData.writeFile(fileName + "/" + fileName + "_" + i + "_with_comments.json", dataInter, () => {
                    console.log(fileName + "_" + i + "_with_comments.json file saved ");
                }, {});
            }

            wikidata.addCommentForRevidData({ data, storeInterData: storeInter }, (err, dataRev) => {
                if (err) {
                    console.log(err);
                } else {
                    storeData.writeFile(filePath.replace(".json", "") + "_with_comments.json", dataRev, () => {
                        console.log(" file saved ");
                        const t1 = new Date().getTime();
                        console.log("Call to 'addComments' took " + (t1 - t0) / 1000 + " seconds.");
                    }, {});
                }
            });
        }, {});
    });

program
    .command("getComment <revid>")
    .description("Get comment data for the given revison id")
    .action((revid) => {

        wikidata.getCommentForRevid(revid, (err, data) => {
            if (err) {
                console.log(err);
            } else {
                console.log(data);
            }
        });
    });

program
    .command("addToxicScore <filePath>")
    .description("Add toxic score to the comments in the given file.")
    .action((filePath) => {
        const t0 = new Date().getTime();
        storeData.readFile(filePath, (data) => {

            toxicScore.addToxicScore(data, (err, dataScore) => {
                if (err) {
                    console.log(err);
                } else {
                    storeData.writeFile(filePath.replace("_with_comments.json", "") + "_with_score.json", dataScore, () => {
                        console.log(" file saved ");
                        const t1 = new Date().getTime();
                        console.log("Call to 'addToxicScore' took " + (t1 - t0) / 1000 + " seconds.");
                    }, {});
                }
            });
        }, {});
    });
/*

//node ./app.js getRecentChanges 2017-01-05:00:00:00 2017-01-05:01:30:00
program
    .version('0.0.1')
    .command('getRecentChanges <start_time> <end_time>')
    .description('Get recent changes on specified time interval.')
    .action((start, end) => {
        let t0 = new Date().getTime();
        wikidata.getRecentChanges(start, end, (err, data) => {
            if (err) {
                console.log(err);
            } else {
                console.log(data.length);
                let t1 = new Date().getTime();
                console.log("Call to 'getRecentChanges' took " + (t1 - t0) / 1000 + " seconds.");

                storeData.writeFile(new Date(start).getTime() + '-' + new Date(end).getTime() + '.json', data,
                    function () {
                        console.log(' file saved ');
                    });
            }
        });
    });

program
    .command('addToxicScore <file_path>')
    .description('Add toxic score to the comments in the given file.')
    .action((file_path) => {
        let t0 = new Date().getTime();
        storeData.readFile(file_path, (data) => {

            toxicScore.addToxicScore(data, (err, data) => {
                if (err) {
                    console.log(err);
                } else {
                    storeData.writeFile(file_path.replace('_with_comments.json', '') + '_with_score.json', data, function () {
                        console.log(' file saved ');
                        let t1 = new Date().getTime();
                        console.log("Call to 'addToxicScore' took " + (t1 - t0) / 1000 + " seconds.");
                    });
                }
            });
        });
    });

program
    .command('getComment <revid>')
    .description('Get comment data for the given revison id')
    .action((revid) => {

        wikidata.getCommentForRevid(revid, (err, data) => {
            if (err) {
                console.log(err);
            } else {
                console.log(data);
            }
        });
    });

program
    .command('getRevisions <pageid>')
    .description('Get all revisons for the given pade id.')
    .action((pageid) => {

        wikidata.getPageRevisions(pageid, (err, data) => {
            if (err) {
                console.log(err);
            } else {
                console.log(data);
            }
        });
    });

program
    .command('validateComments <file_path>')
    .description('Test the generated comments with Wmflabs detox api.')
    .action((file_path) => {
        storeData.readFile(file_path, (data) => {
            testCommentData.testNullCommentsData(data, (err) => {
                if (err) {
                    console.log(err);
                }
            });
        });
    });
*/

// program
//     .command("*")
//     .description("Help")
//     .action(() => {
//         console.log(program.help());
//     });

// program.parse(process.argv);
