// var fs = require('fs');
// const csv = require('fast-csv');
// var stream = fs.createReadStream("wiki_viz_data.tsv");

// var count = 0;
// var csvStream = csv()
//     .on("data", function (data) {
//         count++;//console.log(data[0]);
//     })
//     .on("end", function () {
//         console.log(count, "done");
//     })
//     .on("error", function (err) {
//         console.log(err);
//     });

// stream.pipe(csvStream);
var exec = require('child_process').exec;
const async = require('async');
const config = require('../config/default');
const GetWikiData = require('../wikiDataCollector/getWikiData');
const BigQueryStore = require('../wikiDataCollector/bigQueryStore');
const wikidata = new GetWikiData(config);
const bigquery = new BigQueryStore(config);

var fs = require('fs');

function parseTsvData() {
    var parse = require('csv-parse');

    var csvData = [];
    var csvParseOptions = {
        auto_parse: true, // Ensures that numeric values remain numeric
        columns: true,
        delimiter: '\t',
        quote: '',
        relax: true,
        rowDelimiter: '\n', // This is an issue, I had to set the \n here as 'auto' wasn't working, nor was 'windows'.  Maybe look at auto-detecting line endings?
        skip_empty_lines: true
    };

    var batch = 0;
    fs.createReadStream("wiki_viz_data.tsv")
        .pipe(parse(csvParseOptions))
        .on('data', function (csvrow) {
            //do something with csvrow
            csvData.push(csvrow);

            if (csvData.length === 100000) {
                fs.writeFileSync('data/' + batch + '.json', JSON.stringify(csvData));
                csvData = [];
                batch++;
                console.log(batch, "L");
            }
        })
        .on('end', function () {
            //do something wiht csvData
            fs.writeFileSync('data/' + batch + '.json', JSON.stringify(csvData));
            console.log(csvData.length);
        })
        .on("error", function (err) {
            console.log(err);
        });
}


function testAsync() {
    var N = 100000;
    let revidData = Array.apply(null, { length: N }).map(Number.call, Number)

    var getRevIdAsFunctions = revidData.map((revParams) => {
        let that = this;
        return function (cb) {
            setTimeout(cb, 100);
        };
    });
    async.parallel(getRevIdAsFunctions, (err, results) => {
        if (err) {
            cb(err);
            return;
        }
        console.log(results.length, revidData.length)

    });
}


function splitJson() {
    let jsonData2 = require('../data/176.json');

    // let reset100 = jsonData2.slice(99900, 100000);
    // console.log(reset100.length);
    // fs.writeFileSync('data/176_100.json', JSON.stringify(reset100));

    let jsonData1 = require('../data/176/176_99900_with_comments.json');
    let rest100 = require('../data/176_100_with_comments.json');

    let fullComments = jsonData1.concat(rest100);


    jsonData2.forEach((d, i) => {
        // if (i < 10) {
        d.comment = fullComments[i].comment;
        d.sha1 = fullComments[i].sha1;
        d.revid = fullComments[i].revid;
        //console.log(d);
        //}
    });
    console.log(jsonData2[99991]);
    fs.writeFileSync('data/176_with_comments.json', JSON.stringify(jsonData2));


    //let csvData = jsonData1.concat(jsonData2);
    //  batch = 0;
    //let rest = jsonData.slice(19700);
    //console.log(jsonData1.length, jsonData2.length);
    //console.log(jsonData1[1456], jsonData2[1456]);
    //fs.writeFileSync('data/189_with_comments.json', JSON.stringify(csvData));
    // jsonData1.forEach(function (element, i) {
    //     console.log(element.revid, jsonData2[i].rev_id);
    //     if (element.revid !== jsonData2[i].rev_id) {

    //     }
    //     // if (i % 1000 === 0) {
    //     //     // fs.writeFileSync('data/188-' + batch + '.json', JSON.stringify(jsonData.slice(i, i + 1000)));
    //     //     batch++;
    //     //     console.log(batch, "L");
    //     // }
    // }, this);
    //console.log(csvData.length, "L");

}


function getReadyScoredtData() {

    function isInvalidValid(row) {

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

    function getValidTimestamp(str) {
        let year = str.substr(0, 4);
        let month = str.substr(4, 2);
        let day = str.substr(6, 2);
        let hour = str.substr(8, 2);
        let min = str.substr(10, 2);
        let sec = str.substr(12, 2);
        return year + '-' + month + '-' + day + ' ' + hour + ':' + min + ':' + sec;
    }

    const nameSpaces = {
        1: "talk",
        3: "user_talk"
    }

    for (let start = 178; start >= 175; start--) {



        const fileNumber = start;

        let scoredData = require('../data/scored/scored-' + fileNumber + '_with_comments.json');
        let commentData = require('../data/' + fileNumber + '_with_comments.json');
        const revMap = {};
        commentData.forEach((d) => {
            revMap[d.revid] = d
        });

        let dataToInsert = [];
        //scoredData = scoredData.slice(0, 5);

        scoredData.forEach((d) => {
            if (d.revid) {
                let revId = Math.abs(d.revid);
                let planData = revMap[revId];

                if (revId && planData && planData.comment != '' && planData.rev_timestamp) {
                    let schemaStructure = {
                        timestamp: getValidTimestamp('' + planData.rev_timestamp),
                        namespace: String(nameSpaces[planData.page_namespace]),
                        author: String(planData.rev_user_text),
                        page: String(planData.rev_page),
                        revision_text: String(planData.comment),
                        attack: d.TOXICITY,
                        revision_id: String(planData.revid),
                        revert_id: '',
                        sha1: String(planData.sha1),
                        page_id: String(planData.rev_page)
                    };
                    //console.log(validateSchema(schemaStructure))
                    if (!isInvalidValid(schemaStructure)) {
                        dataToInsert.push(schemaStructure)
                    }
                }
            }
        });
        console.log(scoredData.length, dataToInsert.length, commentData.length);
        let str = '';
        dataToInsert.forEach((d) => {
            str += JSON.stringify(d) + '\n';
        })

        fs.writeFileSync('data/toinsert/' + fileNumber + '.json', str);

    }
    // bigquery.addCommentData(dataToInsert, (err, info) => {
    //     if (err) {
    //         console.log(err, info);
    //     } else {
    //         console.log(info);
    //     }
    // });

}

function insertScoredData() {
    let loadData = [];
    for (let start = 189; start >= 175; start--) {
        loadData.push(start);
    }

    loadData = loadData.map((fileNumber) => {
        return function (cb) {
            let cmd = `bq load --source_format=NEWLINE_DELIMITED_JSON wiki_comments.comments_score data/toInsert/${fileNumber}.json`;
            exec(cmd, function (error, stdout, stderr) {
                if (error !== null) {
                    console.log('exec error: ' + error);
                    cb(error);
                } else {
                    console.log('Done : ----- : ', fileNumber);
                    cb(null, 'Ok')
                }

            });

        }
    });
    let st = new Date().getTime();
    async.series(loadData, (err, results) => {
        if (err) {
            cb(err);
            return;
        }
        console.log("All done , took s", new Date().getTime(- st));
    });
}

insertScoredData();
