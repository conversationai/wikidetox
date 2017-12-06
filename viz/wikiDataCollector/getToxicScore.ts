// jshint esnext:true
/* global require, define,module*/

import * as async from "async";
import * as request from "request";

export class GetToxicScore {

    public API_KEY: string;
    public COMMENT_ANALYZER_URL: string;
    public nameSpaces: object;

    constructor(config) {

        // https://console.cloud.google.com/apis/credentials?project=wikidetox-viz
        // there is a request hit limit to the API , like 1000 / 100 sec
        this.API_KEY = config.API_KEY;
        this.COMMENT_ANALYZER_URL = config.COMMENT_ANALYZER_URL + this.API_KEY;
        this.nameSpaces = {
            1: "talk",
            3: "user_talk",
        };

    }

    // Returns text within the given `commentText` that has the highest toxicity score.
    // If nothing is scored as toxic, it returns empty string.
    public getToxicityScore(commentText, cb, data) {
        const options = {
            body: JSON.stringify({
                comment: {
                    text: commentText,
                },
                requestedAttributes: {
                    TOXICITY: {},
                },
            }),
            uri: this.COMMENT_ANALYZER_URL,
        };
        request.post(options, (error, response, scoreResponse) => {
            if (error) {
                console.log(error, response, scoreResponse);
                cb("Problem scoring comment", error);
                return;
            }
            let worstScore = 0;
            let worstText = "";

            if (typeof scoreResponse === "string") {
                scoreResponse = JSON.parse(scoreResponse);
            }

            if (!scoreResponse.attributeScores && scoreResponse.error) {
                if (scoreResponse.error.code === 429) {
                    cb(null, {
                        text: worstText,
                        toxicityProbability: 0.0,
                    });
                    console.log("COMMENT_ANALYZER_URL Error", scoreResponse);
                    return;
                }
            }

            if (scoreResponse.attributeScores.hasOwnProperty("TOXICITY")) {
                for (const spanScore of scoreResponse.attributeScores.TOXICITY.spanScores) {
                    if (spanScore.score.value > worstScore) {
                        worstScore = spanScore.score.value;
                        worstText = commentText.substr(spanScore.begin, spanScore.end + 1);
                    }
                }
            }
            cb(null, {
                text: worstText,
                toxicityProbability: worstScore,
            });
        });
    }

    public addToxicScore(data, cb) {

        const that = this;

        let commentsData = data;

        if (typeof data === "string") {
            commentsData = JSON.parse(data);
        }

        const emptyComments = [];

        commentsData = commentsData.filter((d) => {
            if (d.comment !== "") {
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

        // commentsData = commentsData.slice(0, 10);

        const getRevIdAsFunctions = commentsData.map((dataRevId) => {
            return (cbRevId) => {
                this.getToxicityScore(dataRevId.comment, cbRevId, dataRevId);
            };
        });

        const getPageTitle = (title) => {
            title = title.split(":");
            title.shift();
            title = title.join(":");
            return title;
        };

        console.log("Found " + commentsData.length + " comments data. Adding toxic score....");

        // call it in series beacause the API has a hit limit
        async.series(getRevIdAsFunctions, (err, results) => {
            if (err) {
                console.log("Error : ", err);
                cb(err);
                return;
            }

            const commentsWtihScore = [];

            results.forEach((scoreData, i) => {
                commentsWtihScore.push({
                    attack: scoreData.toxicityProbability,
                    author: commentsData[i].user,
                    namespace: that.nameSpaces[commentsData[i].ns],
                    page: getPageTitle(commentsData[i].title),
                    page_id: String(commentsData[i].pageid),
                    revert_id: String(commentsData[i].old_revid),
                    revision_id: String(commentsData[i].revid),
                    revision_text: commentsData[i].comment,
                    sha1: commentsData[i].sha1,
                    timestamp: commentsData[i].timestamp,
                });
            });

            emptyComments.forEach((d) => {
                commentsWtihScore.push({
                    attack: 0,
                    author: d.user,
                    namespace: that.nameSpaces[d.ns],
                    page: getPageTitle(d.title),
                    page_id: String(d.pageid),
                    revert_id: String(d.old_revid),
                    revision_id: String(d.revid),
                    revision_text: d.comment,
                    sha1: d.sha1,
                    timestamp: d.timestamp,
                });
            });

            cb(null, commentsWtihScore);

        });
    }
}
