// jshint esnext:true
/* global require, define,module*/

import * as async from "async";
import * as wikibot from "nodemw";
import { CommentCleaner } from "./commentCleaner";

export class GetWikiData {

    public maxLimit: string;
    public client: any;

    constructor() {
        this.maxLimit = "max";
        this.client = new wikibot({
            debug: false, // is more verbose when set to true
            path: "/w", // path to api.php script
            protocol: "https", // Wikipedia now enforces HTTPS
            server: "en.wikipedia.org", // host name of MediaWiki-powered site
        });

    }

    public removeInvalidRevids(data) {
        return data.filter((d) => d.revid);
    }

    public getTextParsed(wikiText) {
        const commentCleaner = new CommentCleaner();
        return commentCleaner.getPlanText(wikiText);
    }

    public getRecentChanges(startDate, endDate, cb) {

        const start = new Date(startDate).toISOString();
        const end = new Date(endDate).toISOString();

        const recentChangesParams = {
            action: "query",
            format: "json",
            list: "recentchanges",
            rcdir: "newer",
            rcend: end,
            rclimit: this.maxLimit,
            rcnamespace: "1|3",
            rcprop: "title|ids|user|timestamp",
            rcstart: start,
        };

        console.log("Fetching recent changes ....");

        this.client.getAll(recentChangesParams, "recentchanges", (err, data) => {
            if (err) {
                cb(err);
            } else {
                cb(null, this.removeInvalidRevids(data));
            }
        });
    }

    public getCommentForRevid(revids, cb) {

        if (!Array.isArray(revids)) {
            revids = [revids];
        }

        const params = {
            action: "query",
            format: "json",
            prop: "revisions",
            revids: revids.join("|"),
            rvdiffto: "prev",
            rvprop: "sha1",
        };
        this.client.api.call(params, (err, info, next, data) => {
            if (err) {
                cb(err);
                return;
            }

            // let pageKeys = Object.keys(data.query.pages);
            const commentData = {
                comment: null,
                revid: null,
                sha1: null,
            };

            try {
                const pageId = Object.keys(data.query.pages)[0];
                let comment = data.query.pages[pageId].revisions[0].diff["*"];
                comment = comment.substring(0, 50000);
                const sha1 = data.query.pages[pageId].revisions[0].sha1;
                commentData.revid = data.query.pages[pageId].revisions[0].diff.to;
                commentData.comment = this.getTextParsed(comment);
                commentData.sha1 = sha1;
            } catch (e) {
                commentData.comment = "";
            }

            cb(null, commentData);

        });
    }

    public addCommentForRevidData(option, cb) {

        let revidData = (Array.isArray(option) || typeof option === "string") ? option : option.data;

        if (typeof revidData === "string") {
            revidData = JSON.parse(revidData);
        }

        // revidData = revidData.slice(0, 50);
        // revidData = revidData.filter(d => (d.revid === 758344931));
        const t0 = new Date().getTime();
        const commentsFetched = [];
        const getRevIdAsFunctions = revidData.map((revParams) => {
            const that = this;
            return (cbRevIdAsFunctions: any) => {

                that.getCommentForRevid(revParams.revid, (err, data) => {
                    if (err) {
                        cbRevIdAsFunctions(err);
                        return;
                    }
                    commentsFetched.push(data);

                    if (commentsFetched.length % 100 === 0) {

                        const t1 = new Date().getTime();
                        console.log("Got " + commentsFetched.length + " comments in " + (t1 - t0) / 1000 + " seconds.");

                        if (option.storeInterData && typeof option.storeInterData === "function") {
                            commentsFetched.forEach((commentData, i) => {
                                // revidData[i].comment = commentData.comment;
                                // revidData[i].sha1 = commentData.sha1;
                                if (Number(commentData.revid) === Number(revidData[i].revid)) {
                                    commentData.rev_id = revidData[i].rev_id;
                                    commentData.rev_timestamp = revidData[i].rev_timestamp;
                                    commentData.rev_page = revidData[i].rev_page;
                                    commentData.page_title = revidData[i].page_title;
                                    commentData.rev_user = revidData[i].rev_user;
                                    commentData.rev_user_text = revidData[i].rev_user_text;
                                    commentData.page_namespace = revidData[i].page_namespace;
                                }
                                // commentData.revid = revidData[i].revid;

                            });

                            option.storeInterData(commentsFetched, commentsFetched.length);

                        }
                    }
                    cbRevIdAsFunctions(null, data);
                });
            };
        });

        console.log("Found " + revidData.length + " revids. Fetching comments data ....");

        async.parallel(getRevIdAsFunctions, (err, results) => {
            if (err) {
                cb(err);
                return;
            }

            revidData.forEach((d, i) => {
                d.comment = results[i].comment;
                d.sha1 = results[i].sha1;
            });
            cb(null, revidData);
        });
    }

    public getPageRevisions(pageid, cb) {
        this.client.getArticleRevisions(Number(pageid), (err, data) => {
            if (err) {
                cb(err);
                return;
            }

            cb(null, data);

        });
    }
}
