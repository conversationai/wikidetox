/*
Copyright 2017 Google Inc.

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
import * as config from './config'
import * as serving from './serving'
import * as supertest from 'supertest'

describe('loading express', function () {
  let server : serving.Server;

  // TODO: Figure out typings for 'done' in beforeEach and afterEach.
  // Currently, the compiler gives confusing errors.
  beforeEach(function (done: any) {
    // TODO(rachelrosen): Figure out if there's a way to write this such that a
    // fake discovery url can be used.
    let serverConfig: config.Config = {
      port: '8080',
      isProduction: false,
      staticPath: "static",
      bigQueryProjectId: "wikidetox-viz",
      bigQueryDataSetId: "wikidetox_conversations",
      bigQueryTable: "conversation_with_score"
    };
    server = new serving.Server(serverConfig);
    server.start().then(done);
  });

  afterEach(function (done: any) {
    server.stop().then(done);
  });

  it('200 to /', function testSlash(done: MochaDone) {
    supertest(server.app)
      .get('/')
      .expect(200, done);
  });

  it('404 to non-existent path /foo/bar', function testPath(done: MochaDone) {
    console.log('test 404')
    supertest(server.app)
      .get('/foo/bar')
      .expect(404, done);
  });
});
