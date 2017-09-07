#!/usr/bin/env node
// jshint esnext:true
/*global require, define,module*/

const program = require('commander');
const async = require('async');


const GetWikiData = require('./getWikiData');
const GetToxicScore = require('./getToxicScore');
const StoreData = require('./storeData');
const TestCommentData = require('./testCommentData');
const BigQueryStore = require('./bigQueryStore');

const config = require('../config/default');


const wikidata = new GetWikiData(config);
const toxicScore = new GetToxicScore(config);
const testCommentData = new TestCommentData(config);
const bigquery = new BigQueryStore(config);

//local store
const storeData = new StoreData('/data');

const streamData = {
    getRecentChanges: function (start, end, cb) {
        wikidata.getRecentChanges(start, end, (err, data) => {
            if (err) {
                cb(err);
            } else {
                cb(null, data);
            }
        });
    },
    addCommentForRevidData: function (data, cb) {
        wikidata.addCommentForRevidData(data, (err, data) => {
            if (err) {
                cb(err);
            } else {
                cb(null, data);
            }
        });
    },
    addToxicScore: function (data, cb) {
        toxicScore.addToxicScore(data, (err, data) => {
            if (err) {
                console.log(err, data);
            } else {
                cb(null, data);
            }
        });
    },
    addDataToBigQueryStore: function (data, cb) {
        bigquery.addCommentData(data, (err, info) => {
            if (err) {
                console.log(err, info);
            } else {
                cb(null, info);
            }
        });
    }
};

const doStreaming = function (start, end, cb) {
    let t0 = new Date().getTime();
    async.waterfall([
        function (cb) {
            streamData.getRecentChanges(start, end, cb);
        },
        function (data, cb) {
            streamData.addCommentForRevidData(data, cb);
        },
        function (data, cb) {
            streamData.addToxicScore(data, cb);
        },
        function (data, cb) {
            streamData.addDataToBigQueryStore(data, cb);
        }
    ], function (err, result) {

        if (err) {
            cb(err)
        }
        cb(null, {
            "result": result,
            "timeTook": (new Date().getTime() - t0) / 1000 + 's'
        })
        console.log("Call took " + (new Date().getTime() - t0) / 1000 + " seconds.");
    });
}

const getMonthData = function (start, end, cb) {
    bigquery.getMonthData(start, end, cb);
}



program
    .version('0.0.1')
    .command('streamData <start_time> <end_time>')
    .description('Collect, score and add data to BigQuery table.')
    .action((start, end) => {
        doStreaming(start, end, function (err, data) {
            if (err) {
                console.log('Error : ', err);
                return;
            }
            console.log(data)
        });
    });


program
    .version('0.0.1')
    .command('flagRevert')
    .description('Mark reverted commits')
    .action((start, end) => {
        bigquery.flagReverted();
    });

program
    .command('addComments <file_path>')
    .description('Find revids for the given file and add comments to it.')
    .action((file_path) => {
        let t0 = new Date().getTime();
        storeData.readFile(file_path, (data) => {


            if (typeof data === 'string') {
                data = JSON.parse(data);
            }
            data.forEach((r) => { r.revid = r.rev_id });
            console.log(data.length);

            function storeInter(data, i) {
                let fileName = file_path.replace('.json', '');

                storeData.createFolder(fileName);
                storeData.clearFolder(fileName);

                storeData.writeFile(fileName + '/' + fileName + '_' + i + '_with_comments.json', data, function () {
                    console.log(fileName + '_' + i + '_with_comments.json file saved ');
                });
            }

            wikidata.addCommentForRevidData({ data: data, storeInterData: storeInter }, (err, data) => {
                if (err) {
                    console.log(err);
                } else {
                    storeData.writeFile(file_path.replace('.json', '') + '_with_comments.json', data, function () {
                        console.log(' file saved ');
                        let t1 = new Date().getTime();
                        console.log("Call to 'addComments' took " + (t1 - t0) / 1000 + " seconds.");
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


program
    .command('*')
    .description('Help')
    .action(() => {
        console.log(program.help())
    });

program.parse(process.argv);

module.exports = {
    doStreaming: doStreaming,
    flagReverted: bigquery.flagReverted.bind(bigquery),
    logStreamTask: bigquery.logStreamTask.bind(bigquery),
    getMonthData: bigquery.getMonthData.bind(bigquery),
    getCalendarData: bigquery.getCalendarData.bind(bigquery)
};
