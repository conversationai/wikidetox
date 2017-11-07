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
import * as conversation from "@conversationai/wpconvlib";

declare var global: any;

// Scaffolding code for runnin in CrowdFlower
export function runWithJqueryLoaded(this:any, $:any) : void {
  //jQuery goes here
  // global.$ = $;

  let rootComment : conversation.Comment | null;
  $('.json-data').each(function (this:any) {
    let conv = JSON.parse($(this)[0].textContent);
    let rootComment = conversation.structureConversaton(conv);
    if (!rootComment) {
      console.error('No Root comment in conversation');
      return;
    }

    // Create a unique id for each conversation so that we can
    // add stuff to that location using jquery.
    let classname = "conv_" + rootComment.id.replace(/\./g, '_');
    $(this).after(`<div class="conversation" id="${classname}"><div>`);
    let conv_el = $(`#${classname}`);

    conversation.walkDfsComments(rootComment,
      (next_comment: conversation.Comment) => {
        conv_el.append(conversation.htmlForComment(next_comment, conv));
      });
  });
}

console.log('running...!');

// A hack to allow runWithJqueryLoaded to be called in a require callback.
global.runWithJqueryLoaded = runWithJqueryLoaded;
