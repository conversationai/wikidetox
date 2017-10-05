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

// private log: Logger;

// export interface Logger {
//   write(s:any): void;
//   error(...args:any[]): void;
// }


// if (this.config.isProduction) {
//   this.log = {
//     write : (_s:any) :void => {},
//     error : (..._args:any[]) :void => {},
//   };
// // TODO(ldixon): do the cloud logging thing...
// // something like this...
// //   // Instantiates a client
// //   const loggingClient = Logging();
// //   // The name of the log to write to
// //   const LOG_NAME = 'convai-server-log';
// //   // Selects the log to write to
// //   let logWrite = loggingClient.log(LOG_NAME).write;
// //   this.log = { write : (s:string) :void => {
// //     // We wrap this just to catch the error so that node doesn't crash
// //     // should stackdriver fail a log statement.
// //     // Once we confirm that stackdriver log functions never fail their promise,
// //     // then this can be removed.
// //     logWrite(s).catch((e:Error) => { console.error(e); });
// //   } };
// // this.app.use(morganLogger('combined'));
// } else {
//   this.log = {
//     write : (s:any) :void => { console.log(s); },
//     error : (...args:any[]) :void => { console.error(args); }
//   };
// }