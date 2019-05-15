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

import { Server } from "./server";
import * as configFile from './config';
const config = configFile.Config;

const server = new Server(config);
server.start()
    .then(() => {
        console.log(`Server started with at port ${config.port}`);
    })
    .catch((e: Error) => {
        console.error(`Server failed to start at port ${config.port}`);
        console.error(e);
        process.exit(1);
    });

server.startClient() // start convai client for comment feedbacks
    .then(() => {
        console.log('Convai client started');
    })
    .catch((e: Error) => {
        console.error(`Client failed to start: ${e.message}`);
        process.exit(1);
    });