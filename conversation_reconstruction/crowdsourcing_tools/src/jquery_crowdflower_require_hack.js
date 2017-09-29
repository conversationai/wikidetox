//
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

// For use in a web-environment where requirejs exists, to load jquery,
// and use the runWithJqueryLoaded function from run.ts
require({
  paths: {
    // "jquery": "https://code.jquery.com/jquery-3.2.1.min",
    "jquery-ui": "https://code.jquery.com/ui/1.11.3/jquery-ui.min",
  },
}, [ "jquery", "jquery-ui" ], window.runWithJqueryLoaded);
