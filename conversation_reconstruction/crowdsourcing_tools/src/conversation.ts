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
  comment_type : 'COMMENT_MODIFICATION' | 'COMMENT_ADDING' | 'SECTION_CREATION';
  status: 'just added' | 'content changed';
  content: string;
  parent_id: string;
  hashed_user_id: string;
  timestamp : string;
  page_title : string;
  // Added based on conversation structure.
  children ?: Comment[];
  isRoot ?: boolean; // true iff this is starting comment of a conversation.
  isLatest ?: boolean; // true iff this is the latest comment in the conversation.
  isFinal ?: boolean; // true iff this is the final (by DFS) comment in the conversation.
}

export interface Conversation { [id:string]: Comment };


export function compareByDateFn(a: Comment, b: Comment) : number {
  return Date.parse(b.timestamp) - Date.parse(a.timestamp);
}

export function indentOfComment(comment: Comment, conversation: Conversation) : number {
  if(comment.parent_id === '') {
    return 0;
  }
  let parent = conversation[comment.parent_id];
  if(!parent) {
    console.error('Comment lacks parent in conversation: ', conversation, comment);
    return 0;
  }
  return 1 + indentOfComment(parent, conversation);
}

export function htmlForComment(comment: Comment, conversation: Conversation) : string {
  let indent = indentOfComment(comment, conversation);

  let comment_class_name : string;
  if (comment.comment_type === 'SECTION_CREATION') {
    comment_class_name = 'section';
  } else if(comment.isLatest) {
    comment_class_name = 'finalcomment';
  } else {
    comment_class_name = 'comment';
  }

  return `
    <div class="${comment_class_name}" style="margin-left: ${indent}em;">
       <div class="content">${comment.content}</div>
       <div class="whenandwho">
        <span>by ${comment.hashed_user_id.substring(0,4)}</span> (<span>${comment.timestamp})</span>
       </div>
     <div>
    `;
}

// Walk down a comment and its children depth first.
export function walkDfsComments(
    rootComment : Comment,
    f : (c:Comment) => void) : void {
  let commentsHtml = [];
  let agenda : Comment[] = [];
  let next_comment : Comment|undefined = rootComment;
  while (next_comment) {
    if (next_comment) {
      if(next_comment.children) {
        agenda = agenda.concat(next_comment.children);
      }
      f(next_comment);
    }
    next_comment = agenda.pop();
  }
}

// Get the last comment in the thread.
export function lastDecendentComment(rootComment : Comment) : Comment {
  let finalComment : Comment = rootComment;
  walkDfsComments(rootComment, (c) => { finalComment = c; });
  return finalComment;
}

// Add and sort children to each comment in a conversation.
// Also set the isRoot field of every comment, and return the
// overall root comment of the conversation.
export function structureConversaton(conversation : Conversation)
    : Comment|null {
  let ids = Object.keys(conversation);

  let rootComment : Comment | null = null;
  let latestComment : Comment | null = null;

  for(let i of ids) {
    let comment = conversation[i];
    comment.isFinal = false;
    comment.isLatest = false;
    if (!latestComment || compareByDateFn(latestComment, comment) > 0) {
      latestComment = comment;
    }
    if(!comment.children) { comment.children = []; }
    let parent = conversation[comment.parent_id];
    if(parent) {
      if(!parent.children) { parent.children = []; }
      parent.children.push(comment);
      parent.children.sort(compareByDateFn);
      comment.isRoot = false;
    } else {
      comment.isRoot = true;
      if (rootComment) {
        console.error('Extra root comments (old and new): ');
        console.error(rootComment);
        console.error(comment);
      }
      rootComment = comment;
    }
  }

  if(latestComment) {
    latestComment.isLatest = true;
  }

  if(rootComment) {
    let finalComment = lastDecendentComment(rootComment);
    finalComment.isFinal = true;
  }

  return rootComment;
}
