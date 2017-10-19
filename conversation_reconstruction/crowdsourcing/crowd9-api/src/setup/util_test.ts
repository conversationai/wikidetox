/*
Copyright 2017 Google Inc.

Licensed under the Apache License, Version 2.0 (the 'License');
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an 'AS IS' BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/
import * as util from './util';
import { expect } from 'chai';

describe('Testing util', function() {
  it('Batcher with stuff to flush', async function() {
    let batchExample : string[] = [];
    let batcher = new util.Batcher<string>(async (batch:string[]) => { batchExample = batch; }, 3);
    await batcher.add('foo1');
    expect(batchExample.length).to.equal(0);
    await batcher.add('foo2');
    expect(batchExample.length).to.equal(0);
    await batcher.add('foo3');
    expect(batchExample.length).to.equal(3);
    expect(batchExample).to.deep.equal(['foo1', 'foo2', 'foo3']);
    await batcher.add('foo4');
    expect(batchExample).to.deep.equal(['foo1', 'foo2', 'foo3']);
    await batcher.add('foo5');
    expect(batchExample).to.deep.equal(['foo1', 'foo2', 'foo3']);
    await batcher.add('foo6');
    expect(batchExample).to.deep.equal(['foo4', 'foo5', 'foo6']);
    await batcher.add('foo7');
    expect(batchExample).to.deep.equal(['foo4', 'foo5', 'foo6']);
    await batcher.add('foo8');
    expect(batchExample).to.deep.equal(['foo4', 'foo5', 'foo6']);
    await batcher.flush();
    expect(batchExample).to.deep.equal(['foo7', 'foo8']);
  });

  it('Batcher nothing to flush', async function() {
    let batchExample : string[] = [];
    let batcher = new util.Batcher<string>(async (batch:string[]) => { batchExample = batch; }, 3);
    await batcher.add('foo1');
    expect(batchExample.length).to.equal(0);
    await batcher.add('foo2');
    expect(batchExample.length).to.equal(0);
    await batcher.add('foo3');
    expect(batchExample.length).to.equal(3);
    expect(batchExample).to.deep.equal(['foo1', 'foo2', 'foo3']);
    await batcher.flush();
    expect(batchExample).to.deep.equal(['foo1', 'foo2', 'foo3']);
  });

  it('Simple applyToLinesOfFile', async function() {
    let concatStrings : string = '';
    await util.applyToLinesOfFile('src/testdata/lines_test.txt', async (line) => {
      concatStrings += line;
    });
    expect(concatStrings).to.equal('foo1foo2foo3foo4foo5foo6foo7foo8');
  });

  it('applyToLinesOfFile with from_line', async function() {
    let concatStrings : string = '';
    await util.applyToLinesOfFile('src/testdata/lines_test.txt', async (line) => {
      concatStrings += line;
    }, { from_line: 3 });
    expect(concatStrings).to.equal('foo3foo4foo5foo6foo7foo8');
  });

  it('applyToLinesOfFile with to_line', async function() {
    let concatStrings : string = '';
    await util.applyToLinesOfFile('src/testdata/lines_test.txt', async (line) => {
      concatStrings += line;
    }, { to_line: 3 });
    expect(concatStrings).to.equal('foo1foo2foo3');
  });

  it('applyToLinesOfFile with to_line and from_line', async function() {
    let concatStrings : string = '';
    await util.applyToLinesOfFile('src/testdata/lines_test.txt', async (line) => {
      concatStrings += line;
    }, { from_line: 3, to_line: 5 });
    expect(concatStrings).to.equal('foo3foo4foo5');
  });
});

