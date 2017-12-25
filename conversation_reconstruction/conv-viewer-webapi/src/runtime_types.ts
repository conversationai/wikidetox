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
  // A fake field to make this type unique: fake nominal typing using npm namespace.
  __type__: '@conversationai/wikidetox/conv-viewer-webapi:runtime_types.RevisionId';
}
export interface ConversationId extends String {
  // A fake field to make this type unique: fake nominal typing using npm namespace.
  __type__: '@conversationai/wikidetox/conv-viewer-webapi:runtime_types.ConversationId';
}


export class RuntimeStringType<T> {
  constructor (public name : string, regexp :string | RegExp) {
    this.valid_regexp = new RegExp(regexp);
  }

  valid_regexp : RegExp;
  assert(x:string) : T {
    if (!this.isValid(x)) {
      throw new RuntimeTypeError(`Wanted ${this.name} but got: ${x}.`);
    }
    return x as any as T;
  }
  isValid(x:string) : boolean {
    return this.valid_regexp.test(x);
  }
}

export let RevisionId = new RuntimeStringType<RevisionId>('RevisionId', /^(\d+)$/);
export let ConversationId = new RuntimeStringType<ConversationId>('ConversationId', /^(\d+\.\d+.\d+)$/);