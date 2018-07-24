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
export interface Comment {
  id: string;
  comment_type: 'MODIFICATION'|'ADDITION'|'CREATION'|'RESTORATION'|'DELETION';
  content: string;
  cleaned_content: string;
  parent_id: string|null;
  replyTo_id: string|null;
  indentation?: number;
  user_text: string;
  timestamp: string;
  page_title: string;
  // If == id then this comment should be highlighted.
  comment_to_highlight?: string;
  // Added based on conversation structure.
  children?: Comment[];
  isRoot?: boolean;  // true iff this is starting comment of a conversation.
  isLatest?:
      boolean;  // true iff this is the latest comment in the conversation.
  isFinal?: boolean;  // true iff this is the final (by DFS) comment in the
                      // conversation.
  isPresent?: boolean; // true iff this version of the comment is present in
                       // the current snapshot.
  latestVersion?: string; // id of the latest version of this comment if isPresent
                          // is false, otherwise id of self.
  dfs_index?: number  // index according to Depth First Search of conv.
}

export interface Conversation { [id: string]: Comment }
;

//
export function interpretId(id: string):
    {revision: number; token: number; action: number}|null {
  let myRegexp = /(\d+)\.(\d+)\.(\d+)/g;
  let match = myRegexp.exec(id);
  if (!match || match.length < 4) {
    return null
  }

  return {
    revision: parseInt(match[1]),
    token: parseInt(match[2]),
    action: parseInt(match[3])
  };
}

export function compareDateFn(da: Date, db: Date): number {
  if (db < da) {
    return 1;
  } else if (da < db) {
    return -1;
  } else {
    return 0;
  }
}

export function compareByDateFn(a: Comment, b: Comment): number {
  let db = Date.parse(b.timestamp);
  let da = Date.parse(a.timestamp);
  return db - da;
}

//
export function compareCommentOrder(comment1: Comment, comment2: Comment) {
  let dateCmp = compareByDateFn(comment2, comment1)
  if (dateCmp !== 0) {
    return dateCmp;
  }

  let id1 = interpretId(comment1.id);
  let id2 = interpretId(comment2.id);

  if (id1 === null || id2 === null) {
    console.warn(
        'Using string comparison for comment order:' +
            ' comment has uninterpretable id: ',
        comment1);
    return comment1.id === comment2.id ? 0 :
                                         (comment1.id > comment2.id ? 1 : -1);
  }

  let revisionDiff = id1.revision - id2.revision;
  let tokenDiff = id1.token - id2.token;
  let actionDiff = id1.action - id2.action;
  return revisionDiff !== 0 ?
      revisionDiff :
      (tokenDiff !== 0 ? tokenDiff : (actionDiff !== 0 ? actionDiff : 0));
}

export function compareCommentOrderSmallestFirst(
    comment1: Comment, comment2: Comment) {
  return compareCommentOrder(comment2, comment1);
}

export function indentOfComment(
    comment: Comment, conversation: Conversation): number {
  if (comment.parent_id === '' || comment.parent_id === null) {
    return 0;
  }
  let parent = conversation[comment.parent_id];
  if (!parent) {
    console.error(
        'Comment lacks parent in conversation: ', conversation, comment);
    return 0;
  }
  return 1 + indentOfComment(parent, conversation);
}

export function htmlForComment(
    comment: Comment, conversation: Conversation): string {
  let indent = indentOfComment(comment, conversation);

  let convId: string = '';
  let section_heading: string = '';
  let comment_class_name: string;
  if (comment.isRoot) {
    comment_class_name = 'comment';
    section_heading = `<div>In page: <b>${comment.page_title}</b></div>`;
    convId = `<div class="convid">
      <span class="convid-text">(conversation id: ${comment.id}) </span>
      <span class="convid-comment-index-header">Comment Number</span>
      </div>`;
  } else if (comment.isLatest) {
    comment_class_name = 'comment finalcomment';
  } else {
    comment_class_name = 'comment';
  }
  let timestamp = comment.timestamp.replace(/ UTC/g, '');

  return `
    ${section_heading}
    ${convId}
    <div class="action ${comment_class_name}" style="margin-left: ${indent}em;">
      <table class="action">
        <tr><td class="whenandwho">
            <div class="author">${comment.user_text}</div>
            <div class="timestamp">${timestamp}</div>
        </td>
        <td class="content">${comment.cleaned_content}</td>
        <td><div class="index">${comment.dfs_index}</div></td>
      </tr>
      </table>
     <div>
    `;
}

// Walk down a comment and its children depth first.
export function walkDfsComments(
    rootComment: Comment, f: (c: Comment) => void): void {
  let commentsHtml = [];
  let agenda: Comment[] = [];
  let next_comment: Comment|undefined = rootComment;
  while (next_comment) {
    if (next_comment.children) {
      agenda = agenda.concat(next_comment.children);
    }
    f(next_comment);
    next_comment = agenda.pop();
  }
}

// Get the last comment in the thread.
export function lastDecendentComment(rootComment: Comment): Comment {
  let finalComment: Comment = rootComment;
  walkDfsComments(rootComment, (c) => {
    finalComment = c;
  });
  return finalComment;
}

// Get the last comment in the thread.
export function indexComments(rootComment: Comment) {
  let index = 0;
  walkDfsComments(rootComment, (c) => {
    c.dfs_index = index;
    index++;
  });
}

export function makeParent(comment: Comment, parent: Comment) {
  if (!comment.isPresent) {
    return;
  }
  if (!parent.children) {
    parent.children = [];
  }
  parent.children.push(comment);
  parent.children.sort(compareCommentOrderSmallestFirst);
  comment.parent_id = parent.id;
  comment.isRoot = false;
}

function selectRootComment(comment: Comment, rootComment: Comment|null) {
  // This can happen when two comments from the same revision occur,
  // and they are the first comment in the conversation.
  // Both the section creation action and the comment have no parent.
  // At this point, we get down to comparing offsets to choose the parent.
  if (!comment.isPresent) {
     return rootComment;
  }
  if (rootComment) {
    let commentCmp = compareCommentOrder(rootComment, comment);
    if (commentCmp < 0) {
      makeParent(comment, rootComment);
    } else if (commentCmp > 0) {
      makeParent(rootComment, comment);
      comment.isRoot = true;
      rootComment = comment;
    } else {
      console.warn(`Duplicate root comment IDs (old and new):
        Choosing root by comment time-stamp.
        Old: ${JSON.stringify(rootComment, null, 2)}
        New: ${JSON.stringify(comment, null, 2)}
      `);
    }
  } else {
    comment.isRoot = true;
    rootComment = comment;
  }
  return rootComment;
}

// Add and sort children to each comment in a conversation.
// Also set the isRoot field of every comment, and return the
// overall root comment of the conversation.
export function structureConversaton(conversation: Conversation): Comment|null {
  let ids = Object.keys(conversation);

  let rootComment: Comment|null = null;
  let latestComments: Comment[] = [];

  for (let i of ids) {
    let comment = conversation[i];
    // If the action is deletion, the content must have been deleted.
    conversation[i].isPresent = true;
    conversation[i].latestVersion = i;
    if (comment.type === 'DELETION') {
      conversation[i].isPresent = false;
      conversation[i].latestVersion = null;
    }
    if (comment.parent_id !== null && comment.parent_id !== ''
    && conversation[comment.parent_id]) {
      conversation[comment.parent_id].isPresent = False;
      conversation[comment.parent_id].latestVersion = i;
      // The previous content has been replaced by the new version.
    }
  }

  for (let i of ids) {
    let comment = conversation[i];
    comment.isFinal = false;
    comment.isLatest = false;
    if (latestComments.length === 0) {
      latestComments = [comment];
    } else {
      let dtime = compareByDateFn(latestComments[0], comment);
      if (dtime > 0) {
        latestComments = [comment];
      } else if (dtime === 0) {
        latestComments.push(comment);
      }
    }

    if (!comment.children) {
      comment.children = [];
    }
    if (comment.replyTo_id !== null && comment.replyTo_id !== '') {
      let parent = conversation[comment.replyTo_id];
      // If the conversation parent is not present, assuming the
      // comment is replying to the parent's latest version.
      while (parent && !parent.isPresent) {
        if (parent.latestVersion) {
          parent = conversation[parent.latestVersion]
        } else {
          parent = conversation[parent.replyTo_id]
        }
      }

      if (parent) {
        makeParent(comment, parent);
      } else {
        console.error(`Parent of this comment is missing from conversation:
         ${JSON.stringify(rootComment, null, 2)}`);
        rootComment = selectRootComment(comment, rootComment);
      }
    } else {
      rootComment = selectRootComment(comment, rootComment);
    }

  }  // For comments.

  // Identify the final comment w.r.t. dfs. i.e. the one at the bottom.
  if (rootComment) {
    indexComments(rootComment);
    let finalComment = lastDecendentComment(rootComment);
    finalComment.isFinal = true;
  }

  // Idenitfy the latest action. Order by lex on time desc then index desc.
  latestComments.sort((c1, c2) => {
    if (c1.dfs_index === undefined || c2.dfs_index === undefined) {
      throw Error('Comments should have dfs_index but do not');
    }
    return c2.dfs_index - c1.dfs_index;
  });
  if (latestComments.length > 0) {
    latestComments[0].isLatest = true;
  }
  return rootComment;
}
