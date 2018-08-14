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
/*

The purpose of this class is to do runtime checking types,
typically those sent by a (potentially malicious) user via the API.

*/

export class RuntimeTypeError extends Error {}

export interface RevisionId extends String {
  // A fake field to make this type unique: fake nominal typing using npm
  // namespace.
  __type__:
      '@conversationai/wikidetox/conv-viewer-webapi:runtime_types.RevisionId';
}
export interface PageId extends String {
  // A fake field to make this type unique: fake nominal typing using npm
  // namespace.
  __type__: '@conversationai/wikidetox/conv-viewer-webapi:runtime_types.PageId';
}
export interface ConversationId extends String {
  // A fake field to make this type unique: fake nominal typing using npm
  // namespace.
  __type__:
      '@conversationai/wikidetox/conv-viewer-webapi:runtime_types.ConversationId';
}
export interface CommentId extends String {
  // A fake field to make this type unique: fake nominal typing using npm
  // namespace.
  __type__:
      '@conversationai/wikidetox/conv-viewer-webapi:runtime_types.CommentId';
}
export interface PageTitleSearch extends String {
  // A fake field to make this type unique: fake nominal typing using npm
  // namespace.
  __type__:
      '@conversationai/wikidetox/conv-viewer-webapi:runtime_types.PageTitleSearch';
}
export interface UserTextSearch extends String {
  // A fake field to make this type unique: fake nominal typing using npm
  // namespace.
  __type__:
      '@conversationai/wikidetox/conv-viewer-webapi:runtime_types.UserTextSearch';
}
export interface UserId extends String {
  // A fake field to make this type unique: fake nominal typing using npm
  // namespace.
  __type__:
      '@conversationai/wikidetox/conv-viewer-webapi:runtime_types.UserId';
}

export interface apiRequest {
  upper_score: number;
  lower_score: number;
  order: string;

  [key : string]: any;
}



export class RuntimeStringType<T extends String> {
  constructor(public name: string, regexp: string|RegExp) {
    this.valid_regexp = new RegExp(regexp);
  }

  valid_regexp: RegExp;
  assert(x: string): T {
    if (!this.isValid(x)) {
      throw new RuntimeTypeError(`Wanted ${this.name} but got: ${x}.`);
    }
    return x as any as T;
  }
  isValid(x: string): boolean {
    return this.valid_regexp.test(x);
  }

  toString(x: T): string {
    return x as any as string;
  }

  fromString(x: string): T {
    return x as any as T;
  }
}

export let RevisionId =
    new RuntimeStringType<RevisionId>('RevisionId', /^(\d+)$/);
export let ConversationId =
    new RuntimeStringType<ConversationId>('ConversationId', /^(\d+\.\d+.\d+)$/);
export let CommentId =
    new RuntimeStringType<CommentId>('CommentId', /^(\d+\.\d+.\d+)$/);
export let PageId = new RuntimeStringType<PageId>('PageId', /^(\d+)$/);
// TODO(ldixon): support escaping for double quotes, or force quote them.
export let PageTitleSearch =
    new RuntimeStringType<PageTitleSearch>('PageTitleSearch', /^([^"]+)$/);
export let UserTextSearch =
    new RuntimeStringType<UserTextSearch>('UserTextSearch', /^([^"]+)$/);
export let UserId =
    new RuntimeStringType<UserId>('UserId', /^(\d+)$/);

export function assertNumber(score : number) {
  if (isNaN(score)) {
    throw new Error(`Wanted number but got: NaN.`);
  }
  return score;
}

export function assertBoolean(bool : boolean) {
  if (bool === true) {return true;}
  if (bool === false) {return undefined;}
  throw new Error(`Wanted boolean but got: +${typeof(bool)}+.`);
}

export function assertOrder(order : string) {
  if (order !== 'DESC' && order !== 'ASC') {
    throw new Error(`Wanted ASC or DESC but got ${order}`);
  }
  return order;
}

export function assertAPIRequest(req : apiRequest) {
  let ret : apiRequest = {upper_score: assertNumber(req.upper_score), lower_score: assertNumber(req.lower_score), order: assertOrder(req.order)};
  if (req.isAlive) {ret.isAlive = assertBoolean(req.isAlive);}
  if (req.page_id) {ret.page_id = PageId.assert(req.page_id);}
  if (req.page_title) {ret.page_title = PageTitleSearch.assert(req.page_title);}
  if (req.user_id) {ret.user_id = UserId.assert(req.user_id);}
  if (req.user_text) {ret.user_text = UserTextSearch.assert(req.user_text);}
  if (req.comment_id) {ret.comment_id = CommentId.assert(req.comment_id);}
  if (req.rev_id) {ret.rev_id = RevisionId.assert(req.rev_id);}
  if (req.conversation_id) {ret.conversation_id = ConversationId.assert(req.conversation_id);}
  console.log(ret);
  console.log(req);
  return ret;
}


