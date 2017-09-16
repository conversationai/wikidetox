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
  // TODO(ldixon): make it always a string, and have it empty string for not present instead of -1
  absolute_replyTo: string | number; // id of the parent
  children ?: Comment[];
  comment_type : 'COMMENT_MODIFICATION' | 'COMMENT_ADDING';
  content: string;
  indentation : string;
  isRoot ?: boolean; // true iff this is starting comment of a conversation.
  // TODO(ldixon): remove
  parent_ids: { [id:string]: boolean };
  // TODO(ldixon): remove
  relative_replyTo : string | number; // relative id of the parent.
  status: 'just added' | 'content changed';
  timestamp : string;
  // TODO(ldixon): remove; not needed and in fact harmful (can be used to game crowdsourcing)
  toxicity_score : number;
  // TODO(ldixon): change up-stream to be a hash of the user-id.
  user_text: string;
}

export interface Conversation { [id:string]: Comment };


export function compareByDateFn(a: Comment, b: Comment) : number {
  return Date.parse(b.timestamp) - Date.parse(a.timestamp);
}

export function htmlForComment(comment: Comment) : string {
  let real_indent = parseInt(comment.indentation) + 1;
  return `
    <div class="conversation" style="margin-left: ${real_indent}em;">
       <div class="content">${comment.content}</div>
       <div class="whenandwho">
        <span>-- ${comment.user_text}</span> (<span>${comment.timestamp})</span>
       </div>
     <div>
    `;
}

// Add and sort children to each comment in a conversation, and also
export function structureConversaton(conversation : Conversation)
    : Comment|null {
  let ids = Object.keys(conversation);

  // Init the children fields.
  for(let i of ids) {
    if(!conversation[i].children) {
      conversation[i].children = [];
    }
  }

  let rootComment : Comment | null = null;

  for(let i of ids) {
    let parent = conversation[conversation[i].absolute_replyTo];
    if(parent && parent.children) {
      parent.children.push(conversation[i]);
      parent.children.sort(compareByDateFn);
      conversation[i].isRoot = false;
    } else {
      conversation[i].isRoot = true;
      if (rootComment) {
        console.error('Extra root comments (old and new): ');
        console.error(rootComment);
        console.error(conversation[i]);
      }
      rootComment = conversation[i];
    }
  }

  return rootComment;
}

// Walk down a comment and its children depth first.
export function walkDfsComments(
    rootComment : Comment,
    f : (c:Comment) => void) {
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
