import * as stream from 'stream';
import * as multiplex_transform from './multiplex_transform';

import { expect } from 'chai';

describe('Multiplex Transform Test', function() {
  it('Simple duplicator', async function() {
    let r = new stream.PassThrough();;
    let m = new multiplex_transform.Multiplex();
    let w1 = new stream.PassThrough();
    let w2 = new stream.PassThrough();

    let w1Stuff : string[] = [];
    let w2Stuff : string[] = [];
    let sStuff : string[] = [];

    let onceW1Data = new Promise((resolve, reject) => {
      w1.on('data', (d: string) => { w1Stuff.push(d); resolve(d); });
    });
    let onceW2Data = new Promise((resolve, reject) => {
      w2.on('data', (d: string) => { w2Stuff.push(d); resolve(d); });
    });

    // TODO(ldixon): fix this, it should be derived from encoding of
    // stream/data piped into m.
    w1.setEncoding('utf-8');
    w2.setEncoding('utf-8');

    m.addOutputStream('w1', w1);
    m.addOutputStream('w2', w2);

    m.setInputProcessor((chunk:string, encoding: string,
        pushFn: (name: string, outChunk:string) => void) => {
      pushFn('w1', chunk);
      pushFn('w2', chunk);
    });
    r.setEncoding('utf-8');

    let s = r.pipe(m);
    let onceFinished = new Promise((resolve, reject) => {
      s.on('finish', () => { resolve() });
    });
    s.on('data', (d:string) => { sStuff.push(d); });
    s.setEncoding('utf-8');
    r.write('hello');
    r.end();

    let w1Data = await onceW1Data;
    let w2Data = await onceW1Data;
    expect(w1Data).to.equal('hello');
    expect(w2Data).to.equal('hello');

    await onceFinished.then(() => {
        expect(w1Stuff).to.have.members(['hello']);
        expect(w2Stuff).to.have.members(['hello']);
        expect(sStuff).to.have.members(['w1', 'w2']);
    });
  });
});