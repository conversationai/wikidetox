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
import { should } from "fuse-test-runner";
import * as conversation from "./conversation";
import { example_conversation1 } from "./testdata/example_conversations";

export class ConversationTest {
   "structureConversaton"() {
      let rootComment =
        conversation.structureConversaton(
          JSON.parse(JSON.stringify(example_conversation1)))
      should(rootComment).beOkay();
      should(rootComment!.isRoot).equal(true);
   }

   "Map of structureConversaton"() {
      let rootComment =
        conversation.structureConversaton(
          JSON.parse(JSON.stringify(example_conversation1)));
      let comment_ids : string[] = [];
      should(rootComment).beOkay();
      should(rootComment!.isRoot).equal(true);

      conversation.walkDfsComments(rootComment!, (c) => {
        comment_ids.push(c.id);
      });

      should(comment_ids).haveLength(4);
      should(comment_ids[0]).equal('550613551.0.0');
      should(comment_ids[1]).equal('675014505.416.416');
      should(comment_ids[2]).equal('685549021.514.514');
      should(comment_ids[3]).equal('700660703.8.8');
    }
}

