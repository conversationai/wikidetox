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
import * as http from 'http';
import * as path from 'path';
import * as bigquery from '@google-cloud/bigquery';

// import * as Logging from '@google-cloud/logging';
// import * as helmet from 'helmet';
// import * as express_enforces_ssl from 'express-enforces-ssl';

// Imports the Google Cloud client library
import * as routes from './routes';
import * as config from './config';
import * as httpcodes from './http-status-codes';

// The main express server class.
export class Server {
  // Public for the sake of writing tests.
  public app : express.Express;
  public httpServer : http.Server;
  public apiKey : string;
  public port: number;
  public staticPath: string;
  public bqClient : bigquery.BigQueryClient;

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

    // Trust proxies so that DDoS tools can see original IP addresses.
    // TODO(ldixon): check is this what we want.
    this.app.set('trust proxy', true);

    // TODO(ldixon): explore how to force ssl.
    // Only force HTTPS on production deployments:
    // https://localhost doesn't have a certificate.
    // Note: to force-serve static content through https, this must be
    // before the static page specification.
    // if (this.config.isProduction) {
      // this.app.use(express_enforces_ssl());
      // this.app.use(helmet);
      // this.app.use(helmet.hsts({ force: true }));
    // }

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

    this.bqClient = new bigquery({ projectId: this.config.bigQueryProjectId });

    routes.setup(this.app, this.config, this.bqClient);

    this.httpServer = http.createServer(this.app);
    console.log(`created server.`);
  }

  public start() : Promise<void> {

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

  async stop() : Promise<void> {
    let onceClosedServer = new Promise<void>((resolve: () => void,
                              _: (impossible_error?: Error) => void) => {
      this.httpServer.close(resolve);
    });
    await onceClosedServer;
  }
};

