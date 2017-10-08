// jshint esnext:true
/* global require, define,module*/


const async = require('async');
const request = require('request');

class GetToxicScore {

    constructor(config) {

        // https://console.cloud.google.com/apis/credentials?project=wikidetox-viz
        // there is a request hit limit to the API , like 1000 / 100 sec
        this.API_KEY = config.API_KEY;
        this.COMMENT_ANALYZER_URL = config.COMMENT_ANALYZER_URL + this.API_KEY;

        this.nameSpaces = {
            1: "talk",
            3: "user_talk"
        }

    }

    // Returns text within the given `commentText` that has the highest toxicity score.
    // If nothing is scored as toxic, it returns empty string.
    getToxicityScore(commentText, cb, data) {
        const options = {
            uri: this.COMMENT_ANALYZER_URL,
            body: JSON.stringify({
                comment: {
                    text: commentText
                },
                requestedAttributes: {
                    TOXICITY: {}
                }
            })
        };
        request.post(options, function (error, response, scoreResponse) {
            if (error) {
                console.log(error, response, scoreResponse)
                cb('Problem scoring comment', error);
                return;
            }
            let worstScore = 0;
            let worstText = '';

            if (typeof scoreResponse === 'string') {
                scoreResponse = JSON.parse(scoreResponse);
            }

            if (!scoreResponse.attributeScores && scoreResponse.error) {
                if (scoreResponse.error.code = 429) {
                    cb(null, {
                        text: worstText,
                        toxicityProbability: 0.0
                    });
                    console.log('COMMENT_ANALYZER_URL Error', scoreResponse);
                    return;
                }
            }

            if (scoreResponse.attributeScores.hasOwnProperty('TOXICITY')) {
                for (let spanScore of scoreResponse.attributeScores.TOXICITY.spanScores) {
                    if (spanScore.score.value > worstScore) {
                        worstScore = spanScore.score.value;
                        worstText = commentText.substr(spanScore.begin, spanScore.end + 1);
                    }
                }
            }
            cb(null, {
                text: worstText,
                toxicityProbability: worstScore
            });
        });
    }


    addToxicScore(data, cb) {

        var that = this;

        let commentsData = data;

        if (typeof data === 'string') {
            commentsData = JSON.parse(data);
        }

        let emptyComments = [];

        commentsData = commentsData.filter((d) => {
            if (d.comment !== '') {
                return true;
            } else {
                emptyComments.push(d);
                return false;
            }
        });

        commentsData = commentsData.filter((d) => {
            if (d.sha1 === undefined) {
                return false;
            }
            if (d.sha1 === null) {
                return false;
            }

            return true;
        });

        if (!commentsData.length) {
            cb("No comments data to add toxicscore");
            return;
        }

        //commentsData = commentsData.slice(0, 10);

        let getRevIdAsFunctions = commentsData.map((data) => {
            let that = this;
            return function (cb) {
                that.getToxicityScore(data.comment, cb, data);
            };
        });

        let getPageTitle = function (title) {
            title = title.split(':');
            title.shift();
            title = title.join(':');
            return title;
        };

        console.log('Found ' + commentsData.length + ' comments data. Adding toxic score....');

        //call it in series beacause the API has a hit limit
        async.series(getRevIdAsFunctions, (err, results) => {
            if (err) {
                console.log('Error : ', err);
                cb(err);
                return;
            }

            var commentsWtihScore = [];

            results.forEach(function (scoreData, i) {
                commentsWtihScore.push({
                    "timestamp": commentsData[i].timestamp,
                    "namespace": that.nameSpaces[commentsData[i].ns],
                    "author": commentsData[i].user,
                    "page": getPageTitle(commentsData[i].title),
                    "revision_text": commentsData[i].comment,
                    "attack": scoreData.toxicityProbability,
                    "page_id": String(commentsData[i].pageid),
                    "revision_id": String(commentsData[i].revid),
                    "revert_id": String(commentsData[i].old_revid),
                    "sha1": commentsData[i].sha1,
                });
            });


            emptyComments.forEach((d) => {
                commentsWtihScore.push({
                    "timestamp": d.timestamp,
                    "namespace": that.nameSpaces[d.ns],
                    "author": d.user,
                    "page": getPageTitle(d.title),
                    "revision_text": d.comment,
                    "attack": 0,
                    "page_id": String(d.pageid),
                    "revision_id": String(d.revid),
                    "revert_id": String(d.old_revid),
                    "sha1": d.sha1,
                });
            })

            cb(null, commentsWtihScore);

        });
    }
}

module.exports = GetToxicScore;
