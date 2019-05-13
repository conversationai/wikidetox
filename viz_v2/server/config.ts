export const Config =  {
    gcloudAPIKey: '[API_KEY]',
    gcloudKeyFilePath: '[Path_to_file]',
    bigQuery: {
        projectId: '[PROJECT_ID]',
        datasetID: '[DATASET_ID]',
        dataTable: '[DATA_TABLE]'
    },
    wikiBot: {
        protocol: 'https',
        server: 'en.wikipedia.org',  // host name of MediaWiki-powered site
        path: '/w',                  // path to api.php script
        debug: true,                // is more verbose when set to true
        username: '[USER_NAME]',
        userAgent: '[USER_AGENT]',             // account to be used when logIn is called (optional)
        password: '[USER_SECRET]'             // password to be used when logIn is called (optional)
    },
    port: 8080
}
