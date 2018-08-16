// jshint esnext:true
/* global require, define,module*/

import * as async from "async";
import * as request from "request";
import { StoreData } from "./StoreData";

const storeData = new StoreData("/data");

export class TestCommentData {

    public testUrl: string;

    constructor(config) {
        this.testUrl = config.wiki.testCommentUrl;
    }

    public makeRequest(urlWithParams, cb) {
        request.get({
            headers: {
                "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36",
            },
            json: true,
            url: urlWithParams,
        }, (error, response, body) => {
            if (!error && response.statusCode === 200) {
                cb(null, body);
            }
            if (error) {
                cb(error);
            }
        });
    }

    public testNullCommentsData(data, cb) {

        let revidData = JSON.parse(data);

        // revidData = revidData.slice(0, 50);

        revidData = revidData.filter((d) => d.comment === "");

        const getRevIdAsFunctions = revidData.map((revParams) => {
            const that = this;
            return (cbRevIdAsFunctions) => {
                const url = that.testUrl + revParams.revid;
                that.makeRequest(url, cbRevIdAsFunctions);
            };
        });

        // getRevIdAsFunctions = getRevIdAsFunctions.slice(0, 25);

        console.log("Found " + revidData.length + " revids with out comments. Testing comments data ....");

        storeData.writeFile("1.empty_comments_data.json", revidData, () => {
            console.log("1.empty_comments_data.json file saved ");
        }, {});

        async.parallelLimit(getRevIdAsFunctions, 50, (err, results) => {
            if (err) {
                console.log("Error : ", err);
                cb(err);
                return;
            }
            const comments = [];
            results.forEach((commentData, i) => {
                if (!commentData.error) {
                    comments.push({
                        revid: revidData[i].revid,
                        text: commentData.text,
                    });
                }
            });

            storeData.writeFile("2.test_data_for_empty_comments.json", comments, () => {
                console.log("2.test_data_for_empty_comments.json file saved ");
                cb(null);
            }, {});

        });
    }
}
