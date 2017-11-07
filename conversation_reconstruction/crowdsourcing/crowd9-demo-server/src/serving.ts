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
import * as bodyParser from 'body-parser';
import * as compression from 'compression';
import * as express from 'express';
// import * as cors from 'cors';
import * as http from 'http';
import * as request from 'request';
import * as path from 'path';

// Imports the Google Cloud client library
import * as config from './config';
// TODO(ldixon): consolidate and remove dup code by
// pushing into a common dependent module.
import * as httpcodes from './http-status-codes';

function getRequest(url: string)
  : Promise<{ status: number, body: string }> {
  return new Promise<{ status: number, body: string }>((resolve, reject) => {
    request.get(url, function (error, response, body) {
      if (!(response && response.statusCode !== undefined)) {
        reject(new Error('no response/response code'));
      } else if (error) {
        reject(error);
      } else {
        resolve({ status: response.statusCode, body: body });
      }
    });
  });
}

// The main express server class.
export class Server {
  // Public for the sake of writing tests.
  public app: express.Express;
  public httpServer: http.Server;
  public apiKey: string;
  public port: number;
  public staticPath: string;

  constructor(public config: config.Config) {
    console.log(`The config is: ${JSON.stringify(this.config, null, 2)}`);
    this.port = parseInt(this.config.port);
    if (!config.staticPath) {
      console.error('staticPath must be specified in the config.');
      return;
    }
    this.staticPath = path.resolve(process.cwd(), config.staticPath);
    console.log(`Resolved staticPath: ${this.staticPath}`);

    this.app = express();

    // var whitelist = ['http://localhost:4200']
    // var corsOptions = {
    //   origin: function (origin:string, callback: (e:Error | null, b?:boolean) => void) {
    //     if (whitelist.indexOf(origin) !== -1) {
    //       callback(null, true)
    //     } else {
    //       callback(new Error('Not allowed by CORS'))
    //     }
    //   }
    // }
    // this.app.use(cors(corsOptions));

    // Trust proxies so that DDoS tools can see original IP addresses.
    // TODO(ldixon): check is this what we want.
    this.app.set('trust proxy', true);

    this.app.use(express.static(this.staticPath));
    // Remove the header that express adds by default.
    this.app.disable('x-powered-by');
    this.app.use(compression());  // Enable gzip
    this.app.use(bodyParser.json());  // Enable json parser

    // Respond to health checks when running on
    // Google AppEngine and ComputeEngine
    this.app.get('/_ah/health', (_req, res) => {
      res.status(httpcodes.OK).send('ok');
    });

    // Returns some work to do, using/hiding the client config
    this.app.get('/api/job_quality', async (_req, res) => {
      try {
        let url = `${this.config.crowd9ApiUrl}/client_jobs/` +
          `${this.config.clientJobKey}/quality_summary`;
        let result = await getRequest(url);
        res.status(result.status).send(result.body);
      } catch (e) {
        console.error(`*** Failed: `, e);
        res.status(httpcodes.INTERNAL_SERVER_ERROR).send('Error: ' + e.message);
      }
    });

    // Returns some work to do, using/hiding the client config
    this.app.get('/api/quality/:workerid', async (req, res) => {
      try {
        let url = `${this.config.crowd9ApiUrl}/client_jobs/` +
          `${this.config.clientJobKey}/workers/` +
          `${req.params.workerid}/quality_summary`;
        let result = await getRequest(url);
        res.status(result.status).send(result.body);
      } catch (e) {
        console.error(`*** Failed: `, e);
        res.status(httpcodes.INTERNAL_SERVER_ERROR).send('Error: ' + e.message);
      }
    });

    // Returns some work to do, using/hiding the client config
    this.app.get('/api/work', async (_req, res) => {
      try {
        let url = `${this.config.crowd9ApiUrl}/client_jobs/` +
          `${this.config.clientJobKey}/next10_unanswered_questions`;
        let result = await getRequest(url);
        res.status(result.status).send(result.body);
      } catch (e) {
        console.error(`*** Failed: `, e);
        res.status(httpcodes.INTERNAL_SERVER_ERROR).send('Error: ' + e.message);
      }
    });

    // Returns some work to do, using/hiding the client config
    this.app.get('/api/work/:client_job_key', async (req, res) => {
      try {
        let url = `${this.config.crowd9ApiUrl}/client_jobs/` +
          `${req.params.client_job_key}/next10_unanswered_questions`;
        let result = await getRequest(url);
        res.status(result.status).send(result.body);
      } catch (e) {
        console.error(`*** Failed: `, e);
        res.status(httpcodes.INTERNAL_SERVER_ERROR).send('Error: ' + e.message);
      }
    });

    // Returns some work to do, using/hiding the client config
    this.app.get('/api/work/:client_job_key/:question_id', async (req, res) => {
      // console.log(JSON.stringify(req.params));
      try {
        let url = `${this.config.crowd9ApiUrl}/client_jobs/` +
          `${req.params.client_job_key}/questions/${req.params.question_id}`;
        // console.log(url);
        let result = await getRequest(url);
        res.status(result.status).send(result.body);
      } catch (e) {
        console.error(`*** Failed: `, e);
        res.status(httpcodes.INTERNAL_SERVER_ERROR).send('Error: ' + e.message);
      }
    });

    // Returns some work to do, using/hiding the client config
    this.app.post('/api/answer', async (req, res) => {
      let response = await this.postAnswer(this.config.clientJobKey, req.body);
      res.status(response.status).send(response.body);
    });

    // Returns some work to do, using/hiding the client config
    this.app.post('/api/answer/:client_job_key', async (req, res) => {
      let response = await this.postAnswer(req.params.client_job_key, req.body);
      res.status(response.status).send(response.body);
    });

    this.httpServer = http.createServer(this.app);
    console.log(`created server`);
  }

  public async postAnswer(clientJobKey: string, answerBody: { [k: string]: string })
    : Promise<{ status: number, body: string }> {
    try {
      let url = `${this.config.crowd9ApiUrl}/client_jobs/` +
        `${clientJobKey}/questions/` +
        `${answerBody.questionId}/answers/${answerBody.userNonce}`;
      console.log('request to: ' + url);
      delete (answerBody.questionId);
      delete (answerBody.userNonce);
      let result = await new Promise<{ status: number, body: string }>(
        (resolve, reject) => {
          request({
            method: 'POST',
            uri: url,
            json: { answer: answerBody }
          },
            function (error, response, body) {
              if (!(response && response.statusCode !== undefined)) {
                reject(new Error('no response/response code'));
              } else if (error) {
                reject(error);
              } else {
                resolve({ status: response.statusCode, body: body });
              }
            });
        });
      return result;
    } catch (e) {
      console.error(`*** Failed: `, e);
      return { status: httpcodes.INTERNAL_SERVER_ERROR, body: 'Error: ' + e.message };
    }
  }

  public start(): Promise<void> {
    return new Promise<void>((resolve: () => void,
      reject: (reason?: Error) => void) => {
      // Start HTTP up the server
      this.httpServer.listen(this.port, (err: Error) => {
        if (err) {
          console.error(err.message);
          reject(err);
          return;
        }
        console.log(`HTTP Listening on port ${this.port}`);
        resolve();
      });
    });
  }

  stop(): Promise<void> {
    return new Promise<void>((resolve: () => void,
      _: (impossible_error?: Error) => void) => {
      this.httpServer.close(resolve);
    });
  }
};

