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
import { example_conversation1,
         example_conversation2,
         example_conversation3,
         example_conversation4
       } from "./testdata/example_conversations";

export class ConversationTest {
  "compareDateFn"() {
    let da = new Date("2007-09-23T09:05:52.000Z");
    let db = new Date("2007-08-23T09:05:52.000Z");
    should(conversation.compareDateFn(da, da)).equal(0);
    should(conversation.compareDateFn(da, db)).equal(1);
    should(conversation.compareDateFn(db, da)).equal(-1);
  }

  "structureConversaton"() {
    let rootComment =
      conversation.structureConversaton(
        JSON.parse(JSON.stringify(example_conversation1)))
    should(rootComment).beOkay();
    should(rootComment!.isRoot).equal(true);
  }

  "structureConversatonWithHeaderAndFirstCommentFromSameRev"() {
    let rootComment =
      conversation.structureConversaton(
        JSON.parse(JSON.stringify(example_conversation4)))
    should(rootComment).beOkay();
    should(rootComment!.isRoot).equal(true);
  }

  "Map of structureConversaton"() {
    let rootComment =
      conversation.structureConversaton(
        JSON.parse(JSON.stringify(example_conversation1)));
    let comment_ids: string[] = [];
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

  "Indent level"() {
    let theConversation = example_conversation1

    let rootComment =
      conversation.structureConversaton(
        JSON.parse(JSON.stringify(theConversation)));
    let comments: conversation.Comment[] = [];
    should(rootComment).beOkay();
    should(rootComment!.isRoot).equal(true);

    conversation.walkDfsComments(rootComment!, (c) => {
      comments.push(c);
    });

    should(comments).haveLength(4);
    should(conversation.indentOfComment(comments[0], theConversation)).equal(0);
    should(conversation.indentOfComment(comments[1], theConversation)).equal(1);
    should(conversation.indentOfComment(comments[2], theConversation)).equal(2);
    should(conversation.indentOfComment(comments[3], theConversation)).equal(1);
  }

  "Comment DFS Index"() {
    let theConversation = example_conversation1

    let rootComment =
      conversation.structureConversaton(
        JSON.parse(JSON.stringify(theConversation)));
    let comments: conversation.Comment[] = [];
    should(rootComment).beOkay();
    should(rootComment!.isRoot).equal(true);

    conversation.walkDfsComments(rootComment!, (c) => {
      comments.push(c);
    });

    should(comments).haveLength(4);
    should(comments[0].dfs_index).equal(0);
    should(comments[1].dfs_index).equal(1);
    should(comments[2].dfs_index).equal(2);
    should(comments[3].dfs_index).equal(3);
  }


  "Interpret & compare id"() {
    let theConversation = example_conversation2
    let rootComment =
      conversation.structureConversaton(
        JSON.parse(JSON.stringify(theConversation)));
    let comments: conversation.Comment[] = [];
    should(rootComment).beOkay();
    should(rootComment!.isRoot).equal(true);

    conversation.walkDfsComments(rootComment!, (c) => {
      comments.push(c);
    });

    let id1 = conversation.interpretId(comments[0].id);
    should(id1!.revision).equal(550613551);
    should(id1!.token).equal(0);
    should(id1!.action).equal(0);

    let id2 = conversation.interpretId(comments[1].id);
    should(id2!.revision).equal(675014505);
    should(id2!.token).equal(416);
    should(id2!.action).equal(416);

    let id3 = conversation.interpretId(comments[2].id);
    should(id3!.revision).equal(675014505);
    should(id3!.token).equal(20);
    should(id3!.action).equal(416);

    should(conversation.compareCommentOrder(comments[0], comments[1]) < 0)
      .beTrue();
    should(conversation.compareCommentOrder(comments[1], comments[0]) < 0)
      .beFalse();
    should(conversation.compareCommentOrder(comments[0], comments[0]) === 0)
      .beTrue();
    should(conversation.compareCommentOrder(comments[2], comments[1]) < 0)
      .beTrue();
    should(conversation.compareCommentOrder(comments[1], comments[2]) < 0)
      .beFalse();
  }


  "structure conversations with multiple roots treated sensibly"() {
    let theConversation = example_conversation3
    let rootComment =
      conversation.structureConversaton(
        JSON.parse(JSON.stringify(theConversation)));
    let comments: conversation.Comment[] = [];
    should(rootComment).beOkay();
    should(rootComment!.isRoot).equal(true);
    should(rootComment!.id).equal('675014505.20.416');

    conversation.walkDfsComments(rootComment!, (c) => {
      comments.push(c);
    });
    console.log(comments);

    should(comments).haveLength(2);
    should(conversation.indentOfComment(comments[0], theConversation)).equal(0);
    should(conversation.indentOfComment(comments[1], theConversation)).equal(1);

    let id1 = conversation.interpretId(comments[0].id);
    should(id1!.revision).equal(675014505);
    should(id1!.token).equal(20);
    should(id1!.action).equal(416);

    let id2 = conversation.interpretId(comments[1].id);
    should(id2!.revision).equal(675014505);
    should(id2!.token).equal(416);
    should(id2!.action).equal(416);

    should(conversation.compareCommentOrder(comments[0], comments[1]) < 0)
      .beTrue();
  }
}

