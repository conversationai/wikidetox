// Copy this file to `config/default.js` and enter the `gcloudKey` and `API_KEY`
var appConfig = {
    gcloudKey: '<Path to google cloud key json file>',
    API_KEY: '<Google Cloud Perspective API Key>',
    bigQuery: {
        projectId: 'wikidetox-viz',
        dataSetId: 'wiki_comments',
        revisionsTable: 'comments_score',
        revertedTable: 'comments_reverted',
        cronLogs: 'tasks_schedule_logs'
    },
    startStremingTime: '2017-06-17T00:00:00.000Z',
    wiki: {
        testCommentUrl: 'https://tools.wmflabs.org/detox/api?model=attack&input_type=rev_id&input='
    },
    COMMENT_ANALYZER_URL: 'https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze?key=',
    SUGGEST_SCORE_URL: 'https://commentanalyzer.googleapis.com/v1alpha1/comments:suggestscore?key='
};

module.exports = appConfig;
