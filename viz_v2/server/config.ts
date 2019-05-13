/*
Copyright 2019 Google Inc.
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
    http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

export const Config =  {
    gcloudKey: '[Path_to_file]',
    bigQuery: {
        projectId: '[PROJECT_ID]',
        datasetID: '[DATESET]',
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
