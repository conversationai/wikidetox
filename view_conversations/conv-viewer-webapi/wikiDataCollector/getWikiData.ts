// jshint esnext:true
/* global require, define,module*/

import * as async from "async";
import * as wikibot from "nodemw";

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
        return data.filter((d) => (d.revid);
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
            rcnamespace: "1|3|5|7|9|11|13|16|101|109|119|447|711|829|2301|2303",
            rcprop: "title|ids|user|userid|timestamp",
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

    public getCommentForRevid(revidPairs, cb) {

        // TODO(yiqingh): Shouldn't here be a single pair?
        if (!Array.isArray(revidPairs)) {
            revidPairs = [revidPairs];
        }
        revids = [];

        const params = {
            action: "query",
            format: "json",
            prop: "revisions",
            revids: revids.join("|"),
            rvprop: "sha1",
        };
        this.client.api.call(params, (err, info, next, data) => {
            if (err) {
                cb(err);
                return;
            }

            // let pageKeys = Object.keys(data.query.pages);
            const revisionData = {
                last_revision: null,
                // How to distinguish last revision?
                content: null,
                revid: null,
                sha1: null,
            };

            try {
                const pageId = Object.keys(data.query.pages)[0];
                revisiondata.content = data.query.pages[pageId].revisions[0].content;
                const sha1 = data.query.pages[pageId].revisions[0].sha1;
                revisionData.revid = data.query.pages[pageId].revisions[0].revid;
                reivisonData.sha1 = data.query.pages[pageId].revisions[0].sha1;
                //TODO(yiqingh): Add reconstruction functionality here
            } catch (e) {
                revisionData = null;
            }

            cb(null, revisionData);

        });
    }

    public addCommentForRevidData(option, cb) {

        let revidData = (Array.isArray(option) || typeof option === "string") ? option : option.data;

        if (typeof revidData === "string") {
            revidData = JSON.parse(revidData);
        }

        const t0 = new Date().getTime();
        const revisionsFetched = [];
        //TODO (yiqingh): change this part
        const getRevIdAsFunctions = revidData.map((revParams) => {
            const that = this;
            return (cbRevIdAsFunctions: any) => {

                that.getCommentForRevid((revParams.revid, revParams.old_revid), (err, data) => {
                    if (err) {
                        cbRevIdAsFunctions(err);
                        return;
                    }
                    revisionsFetched.push(data);

                    if (revisionsFetched.length % 100 === 0) {

                        const t1 = new Date().getTime();
                        console.log("Got " + revisionsFetched.length + " comments in " + (t1 - t0) / 1000 + " seconds.");

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
