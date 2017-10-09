// jshint esnext:true
/* global require, define,module*/


const async = require('async');
const request = require('request');
const StoreData = require('./storeData');

const storeData = new StoreData('/data');

class TestCommentData {

    constructor(config) {

        this.testUrl = config.wiki.testCommentUrl;

    }

    makeRequest(urlWithParams, cb) {
        request.get({
            url: urlWithParams,
            json: true,
            headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'
            }
        }, (error, response, body) => {
            if (!error && response.statusCode == 200) {
                cb(null, body);
            }
            if (error) {
                cb(error);
            }
        });
    }

    testNullCommentsData(data, cb) {

        let revidData = JSON.parse(data);

        // revidData = revidData.slice(0, 50);

        revidData = revidData.filter(d => d.comment === '');

        var getRevIdAsFunctions = revidData.map((revParams) => {
            let that = this;
            return function (cb) {
                let url = that.testUrl + revParams.revid;
                that.makeRequest(url, cb);
            };
        });

        //getRevIdAsFunctions = getRevIdAsFunctions.slice(0, 25);

        console.log('Found ' + revidData.length + ' revids with out comments. Testing comments data ....');

        storeData.writeFile('1.empty_comments_data.json', revidData, function () {
            console.log('1.empty_comments_data.json file saved ');
        });

        async.parallelLimit(getRevIdAsFunctions, 50, (err, results) => {
            if (err) {
                console.log('Error : ', err);
                cb(err);
                return;
            }
            var comments = [];
            results.forEach(function (commentData, i) {
                if (!commentData.error) {
                    comments.push({
                        text: commentData.text,
                        revid: revidData[i].revid
                    });
                }
            });

            storeData.writeFile('2.test_data_for_empty_comments.json', comments, function () {
                console.log('2.test_data_for_empty_comments.json file saved ');
                cb(null);
            });

        });
    }
}

module.exports = TestCommentData;
