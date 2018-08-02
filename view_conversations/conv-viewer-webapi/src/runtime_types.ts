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

export function assertNumber(score : number) {
  if (isNaN(score)) {
    throw new Error(`Wanted number but got: NaN.`);
  }
  return score;
}

export function assertOrder(order : string) {
  if (order !== 'DESC' && order !== 'ASC') {
    throw new Error(`Wanted ASC or DESC but got ${order}`);
  }
  return order;
}


