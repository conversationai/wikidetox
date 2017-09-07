// jshint esnext:true
/* global require, define,module*/

const wikibot = require('nodemw');
const CommentCleaner = require('./commentCleaner');
const async = require('async');

class GetWikiData {

    constructor() {

        this.maxLimit = 'max';

        this.client = new wikibot({
            protocol: 'https', // Wikipedia now enforces HTTPS
            server: 'en.wikipedia.org', // host name of MediaWiki-powered site
            path: '/w', // path to api.php script
            debug: false // is more verbose when set to true
        });

    }

    removeInvalidRevids(data) {
        return data.filter(d => d.revid);
    }

    getTextParsed(wikiText) {
        let commentCleaner = new CommentCleaner();
        return commentCleaner.getPlanText(wikiText);
    }

    getRecentChanges(startDate, endDate, cb) {

        let start = new Date(startDate).toISOString();
        let end = new Date(endDate).toISOString();

        let recentChangesParams = {
            "action": "query",
            "format": "json",
            "list": "recentchanges",
            "rcstart": start,
            "rcend": end,
            "rcnamespace": "1|3",
            "rcprop": "title|ids|user|timestamp",
            "rclimit": this.maxLimit,
            "rcdir": "newer"
        };

        console.log('Fetching recent changes ....');

        this.client.getAll(recentChangesParams, 'recentchanges', (err, data) => {
            if (err) {
                cb(err);
            } else {
                cb(null, this.removeInvalidRevids(data));
            }
        });
    }


    getCommentForRevid(revids, cb) {

        if (!Array.isArray(revids)) {
            revids = [revids];
        }

        let params = {
            "action": "query",
            "format": "json",
            "prop": "revisions",
            "rvdiffto": "prev",
            "revids": revids.join('|'),
            "rvprop": "sha1"
        };
        this.client.api.call(params, (err, info, next, data) => {
            if (err) {
                cb(err);
                return;
            }

            //let pageKeys = Object.keys(data.query.pages);
            let commentData = {};

            try {
                let page_id = Object.keys(data.query.pages)[0];
                let comment = data.query.pages[page_id]['revisions'][0]['diff']['*'];
                comment = comment.substring(0, 50000);
                let sha1 = data.query.pages[page_id]['revisions'][0]['sha1'];
                commentData.revid = data.query.pages[page_id]['revisions'][0]['diff'].to;
                commentData.comment = this.getTextParsed(comment);
                commentData.sha1 = sha1;
            } catch (e) {
                commentData.comment = '';
            }


            cb(null, commentData);

        });
    }

    addCommentForRevidData(option, cb) {

        let revidData = (Array.isArray(option) || typeof option === 'string') ? option : option.data;

        if (typeof revidData === 'string') {
            revidData = JSON.parse(data);
        }

        // revidData = revidData.slice(0, 50);
        // revidData = revidData.filter(d => (d.revid === 758344931));
        let t0 = new Date().getTime();
        var commentsFetched = [];
        var getRevIdAsFunctions = revidData.map((revParams) => {
            let that = this;
            return function (cb) {

                that.getCommentForRevid(revParams.revid, (err, data) => {
                    if (err) {
                        cb(err);
                        return;
                    }
                    commentsFetched.push(data);


                    if (commentsFetched.length % 100 === 0) {

                        let t1 = new Date().getTime();
                        console.log("Got " + commentsFetched.length + " comments in " + (t1 - t0) / 1000 + " seconds.");

                        if (option.storeInterData && typeof option.storeInterData === 'function') {
                            commentsFetched.forEach(function (commentData, i) {
                                //revidData[i].comment = commentData.comment;
                                //revidData[i].sha1 = commentData.sha1;
                                if (commentData.revid == revidData[i].revid) {
                                    commentData.rev_id = revidData[i].rev_id;
                                    commentData.rev_timestamp = revidData[i].rev_timestamp;
                                    commentData.rev_page = revidData[i].rev_page;
                                    commentData.page_title = revidData[i].page_title;
                                    commentData.rev_user = revidData[i].rev_user;
                                    commentData.rev_user_text = revidData[i].rev_user_text;
                                    commentData.page_namespace = revidData[i].page_namespace;
                                }
                                //commentData.revid = revidData[i].revid;

                            });

                            option.storeInterData(commentsFetched, commentsFetched.length);

                        }
                    }
                    cb(null, data);
                });
            };
        });

        console.log('Found ' + revidData.length + ' revids. Fetching comments data ....');

        async.parallel(getRevIdAsFunctions, (err, results) => {
            if (err) {
                cb(err);
                return;
            }

            revidData.forEach(function (d, i) {
                d.comment = results[i].comment;
                d.sha1 = results[i].sha1;
            });
            cb(null, revidData);

        });
    }

    getPageRevisions(pageid, cb) {
        this.client.getArticleRevisions(Number(pageid), (err, data) => {
            if (err) {
                cb(err);
                return;
            }

            cb(null, data);

        });
    }
}

module.exports = GetWikiData;
