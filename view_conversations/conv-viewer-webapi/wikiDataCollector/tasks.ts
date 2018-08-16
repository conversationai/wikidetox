#!/usr/bin/env node
// jshint esnext:true

import * as async from "async";
import * as program from "commander";
import * as fs from "fs";

import { SpannerStore } from "./SpannerStore";
import { GetWikiData } from "./getWikiData";
import { StoreData } from "./StoreData";
import { TestCommentData } from "./testCommentData";

// TODO : pass this as params
const configPath = "config/production.json";
const config = JSON.parse(fs.readFileSync(configPath, "utf8"));

const wikidata = new GetWikiData();
const testCommentData = new TestCommentData(config);
const spanner = new SpannerStore(config);

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

export class Tasks {

    public doStreaming = doStreaming;
    public logStreamTask = bigquery.logStreamTask.bind(bigquery);
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
