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
         example_conversation4,
         example_conversation5
       } from "./testdata/example_conversations";

export class ConversationTest {
  public "compareDateFn"() {
    const da = new Date("2007-09-23T09:05:52.000Z");
    const db = new Date("2007-08-23T09:05:52.000Z");
    should(conversation.compareDateFn(da, da)).equal(0);
    should(conversation.compareDateFn(da, db)).equal(1);
    should(conversation.compareDateFn(db, da)).equal(-1);
  }

  public "structureConversaton"() {
    const rootComment =
      conversation.structureConversaton(
        JSON.parse(JSON.stringify(example_conversation1)))
    should(rootComment).beOkay();
    should(rootComment!.isRoot).equal(true);
  }

  public "structureConversatonWithHeaderAndFirstCommentFromSameRev"() {
    const rootComment =
      conversation.structureConversaton(
        JSON.parse(JSON.stringify(example_conversation4)))
    should(rootComment).beOkay();
    should(rootComment!.isRoot).equal(true);
  }

  public "Map of structureConversaton"() {
    const rootComment =
      conversation.structureConversaton(
        JSON.parse(JSON.stringify(example_conversation1)));
    const commentIds: string[] = [];
    should(rootComment).beOkay();
    should(rootComment!.isRoot).equal(true);

    conversation.walkDfsComments(rootComment!, (c) => {
      commentIds.push(c.id);
    });

    should(commentIds).haveLength(5);
    should(commentIds[0]).equal('99858.17787.17782');
    should(commentIds[1]).equal('99939.17811.17811');
    should(commentIds[2]).equal('99999.18044.18044');
    should(commentIds[3]).equal('100001.18478.18478');
    should(commentIds[4]).equal('100037.18908.18908');
  }

  
  public "Indent level"() {
    const theConversation = example_conversation1

    const rootComment =
      conversation.structureConversaton(
        JSON.parse(JSON.stringify(theConversation)));
    const comments: conversation.Comment[] = [];
    should(rootComment).beOkay();
    should(rootComment!.isRoot).equal(true);

    conversation.walkDfsComments(rootComment!, (c) => {
      comments.push(c);
    });

    should(comments).haveLength(5);
    should(comments[0].indentation).equal(0);
    should(comments[1].indentation).equal(1);
    should(comments[2].indentation).equal(2);
    should(comments[3].indentation).equal(2);
    should(comments[4].indentation).equal(3);
  }

  public "Comment DFS Index"() {
    const theConversation = example_conversation1

    const rootComment =
      conversation.structureConversaton(
        JSON.parse(JSON.stringify(theConversation)));
    const comments: conversation.Comment[] = [];
    should(rootComment).beOkay();
    should(rootComment!.isRoot).equal(true);

    conversation.walkDfsComments(rootComment!, (c) => {
      comments.push(c);
    });

    should(comments).haveLength(5);
    should(comments[0].dfs_index).equal(0);
    should(comments[1].dfs_index).equal(1);
    should(comments[2].dfs_index).equal(2);
    should(comments[3].dfs_index).equal(3);
    should(comments[4].dfs_index).equal(4);
  }

  public "Interpret & compare id"() {
    const theConversation = example_conversation2
    const rootComment =
      conversation.structureConversaton(
        JSON.parse(JSON.stringify(theConversation)));
    const comments: conversation.Comment[] = [];
    should(rootComment).beOkay();
    should(rootComment!.isRoot).equal(true);

    conversation.walkDfsComments(rootComment!, (c) => {
      comments.push(c);
    });

    const id1 = conversation.interpretId(comments[0].id);
    should(id1!.revision).equal(550613551);
    should(id1!.token).equal(0);
    should(id1!.action).equal(0);

    const id2 = conversation.interpretId(comments[1].id);
    should(id2!.revision).equal(675014505);
    should(id2!.token).equal(416);
    should(id2!.action).equal(416);

    const id3 = conversation.interpretId(comments[2].id);
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

  public "Map of structureConversaton with deleted comments"() {
    const rootComment =
      conversation.structureConversaton(
        JSON.parse(JSON.stringify(example_conversation5)));
    const commentIds: string[] = [];
    should(rootComment).beOkay();
    should(rootComment!.isRoot).equal(true);

    conversation.walkDfsComments(rootComment!, (c) => {
      commentIds.push(c.id);
    });

    should(commentIds).haveLength(4);
    should(commentIds[0]).equal('99858.17787.17782');
    should(commentIds[1]).equal('99999.18044.18044');
    should(commentIds[2]).equal('100001.18478.18478');
    should(commentIds[3]).equal('100037.18908.18908');
  }



  // TODO (yiqingh, ldixon): not sure what this test is for
  /*
  public "structure conversations with multiple roots treated sensibly"() {
    const theConversation = example_conversation3
    const rootComment =
      conversation.structureConversaton(
        JSON.parse(JSON.stringify(theConversation)));
    const comments: conversation.Comment[] = [];
    should(rootComment).beOkay();
    should(rootComment!.isRoot).equal(true);
    should(rootComment!.id).equal('675014505.20.416');

    conversation.walkDfsComments(rootComment!, (c) => {
      comments.push(c);
    });
    console.error(comments);

    should(comments).haveLength(2);
    should(comments[0].indentation).equal(0);
    should(comments[1].indentation).equal(1);

    const id1 = conversation.interpretId(comments[0].id);
    should(id1!.revision).equal(675014505);
    should(id1!.token).equal(20);
    should(id1!.action).equal(416);

    const id2 = conversation.interpretId(comments[1].id);
    should(id2!.revision).equal(675014505);
    should(id2!.token).equal(416);
    should(id2!.action).equal(416);

    should(conversation.compareCommentOrder(comments[0], comments[1]) < 0)
      .beTrue();
  }
   */
}

